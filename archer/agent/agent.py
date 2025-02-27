import logging

from langchain_arcade import ArcadeToolManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.errors import NodeInterrupt
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from archer.agent.base import BaseAgent
from archer.defaults import TOOLKITS

logger = logging.getLogger(__name__)


class AgentState(MessagesState):
    # Save the authorization URLs by tool name and URL.
    auth_urls: list[tuple[str, str]] | None = None


class LangGraphAgent(BaseAgent):
    """
    A streamlined LangGraph agent that handles tool calls using robust message
    extraction and integrates Arcade-based authorization when needed.
    """

    def __init__(self, model: str = "gpt-4o", tools: list[str] | None = None):
        super().__init__(model=model)
        self.llm = ChatOpenAI(model=model)
        self.prompt = ChatPromptTemplate.from_messages([("placeholder", "{messages}")])
        self.manager = ArcadeToolManager()
        self.tools = self.manager.get_tools(tools=tools, toolkits=TOOLKITS)
        self.tool_node = ToolNode(self.tools)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.prompted_model = self.prompt | self.llm_with_tools
        self.setup_graph()

    def get_tool_descriptions(self) -> dict[str, str]:
        """
        Extract tool names and descriptions.
        """
        tool_descriptions = {}
        for tool in self.tools:
            name = getattr(tool, "name", None)
            description = getattr(tool, "description", None)
            if name and description:
                tool_descriptions[name] = description
        return tool_descriptions

    def invoke(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        Process the state through the graph and allow exceptions to propagate.
        """
        try:
            result = self.graph.invoke(state, config=config)
        except Exception:
            logger.exception("Error during agent invocation")
            raise
        return result

    def call_agent(self, state: AgentState, config: RunnableConfig) -> dict:
        """
        Call the LLm with its tools. This method extracts the assistant's reply and
        any tool calls without assuming their position.
        """
        messages = state["messages"]
        # Generate response using the prompted model
        response = self.prompted_model.invoke({"messages": messages})

        # Extract the assistant's reply and any tool calls
        return {"messages": [response]}

    def should_continue(self, state: AgentState, config: RunnableConfig) -> str:
        """
        Continue to the auth check if any message contains a tool call.
        """
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "check_auth"
        return END

    def check_auth(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        Check if the tool call(s) require user authorization.
        """
        user_id = config.get("configurable", {}).get("user_id")
        auth_list = []

        # get the tool calls from the last message
        for tool_call in state["messages"][-1].tool_calls:
            tool_name = tool_call["name"]
            if self.manager.requires_auth(tool_name):
                auth_response = self.manager.authorize(tool_name, user_id)
                if auth_response.status != "completed":
                    auth_list.append((tool_name, auth_response.url))
        return {"auth_urls": auth_list}

    def authorize(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        Raise a NodeInterrupt if authorization is pending.
        """

        if state["auth_urls"]:
            # If multiple tools require auth, list them; otherwise, use the single message.
            if len(state["auth_urls"]) == 1:
                tool_auth = state["auth_urls"][0]
                auth_message = (
                    f"Please authorize the *{tool_auth[0]}* tool by visiting:\n{tool_auth[1]}\n"
                    "Once authorized, resend the message."
                )
            else:
                auth_message = "Please authorize access for the following tools:\n"
                for i, tool_auth in enumerate(state["auth_urls"], 1):
                    auth_message += f"{i}. *{tool_auth[0]}*: {tool_auth[1]}\n"
                auth_message += "After authorizing, please resend the message."

            # clear the auth_urls from the state
            state["auth_urls"] = None

            # TODO Raise the interrupt so the client can capture and then re-invoke with a correction ToolMessage if needed.
            raise NodeInterrupt(auth_message)
        return state

    def setup_graph(self) -> None:
        """
        Build the conversation workflow graph.
        """
        self.workflow = StateGraph(AgentState)

        # Add nodes to the graph
        self.workflow.add_node("agent", self.call_agent)
        self.workflow.add_node("tools", self.tool_node)
        self.workflow.add_node("authorize", self.authorize)
        self.workflow.add_node("check_auth", self.check_auth)

        # Define the edges and control flow
        self.workflow.add_edge(START, "agent")
        self.workflow.add_conditional_edges("agent", self.should_continue, ["check_auth", END])
        self.workflow.add_edge("check_auth", "authorize")
        self.workflow.add_edge("authorize", "tools")
        self.workflow.add_edge("tools", "agent")

        # Compile the graph
        self.graph = self.workflow.compile()
