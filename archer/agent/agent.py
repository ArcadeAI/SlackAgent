import logging

from langchain_arcade import ArcadeToolManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.errors import NodeInterrupt
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from archer.agent.base import BaseAgent

logger = logging.getLogger(__name__)


class AgentState(MessagesState):
    auth_url: str | None = None


class LangGraphAgent(BaseAgent):
    """
    An agent that uses LangGraph to process messages and manage tools.
    """

    def __init__(
        self, model: str = "gpt-4", tools: list[str] = None
    ):  # TODO: add other providers
        super().__init__(model=model)
        self.llm = ChatOpenAI(model=model)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("placeholder", "{messages}"),
            ]
        )
        self.manager = ArcadeToolManager()
        self.tools = self.manager.get_tools()
        self.tool_node = ToolNode(self.tools)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.prompted_model = self.prompt | self.llm_with_tools
        self.setup_graph()

    def invoke(self, state: dict, config: dict) -> dict:
        """
        Process the given state and configuration, and return the new state.
        """
        try:
            result = self.graph.invoke(state, config=config)
            return result
        except NodeInterrupt as e:
            logger.info(f"Authorization required: {e}")
            # Add the interrupt message to the state
            state["interrupt_message"] = str(e)
            return state
        except Exception as e:
            logger.exception("Error during agent invocation")
            raise e

    def call_agent(self, state: AgentState, config: dict) -> dict:
        """
        Use the LLM with tools to generate a response and update the state.
        """
        messages = state["messages"]
        # Generate response using the prompted model
        response = self.prompted_model.invoke({"messages": messages})
        # Update the state with the assistant's message
        return {"messages": [response]}

    def should_continue(self, state: AgentState, config: dict) -> str:
        """
        Determine the next node based on the presence of tool calls.
        """
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "check_auth"
        # If no tool calls are present, end the workflow
        return END

    def check_auth(self, state: AgentState, config: dict):
        user_id = config["configurable"].get("user_id")

        # TODO multiple tool calls to check here.
        tool_name = state["messages"][-1].tool_calls[0]["name"]
        auth_response = self.manager.authorize(tool_name, user_id)
        if auth_response.status != "completed":
            return {"auth_url": auth_response.url}
        else:
            return {"auth_url": None}

    def authorize(self, state: AgentState, config: dict) -> AgentState:
        """
        Handle tool authorization by raising a NodeInterrupt with the auth message.
        """
        if state.get("auth_url"):
            auth_message = f"Please authorize access to the tool by visiting this URL:\n\n{state['auth_url']}"
            # Raise NodeInterrupt with the auth message
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
        self.workflow.add_conditional_edges(
            "agent", self.should_continue, ["check_auth", END]
        )
        self.workflow.add_edge("check_auth", "authorize")
        self.workflow.add_edge("authorize", "tools")
        self.workflow.add_edge("tools", "agent")

        # Compile the graph
        self.graph = self.workflow.compile()
