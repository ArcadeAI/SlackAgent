import logging

from langchain_arcade import ArcadeToolManager
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.errors import NodeInterrupt
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from archer.agent.base import BaseAgent
from archer.defaults import TOOLKITS, get_system_content

logger = logging.getLogger(__name__)

class AgentState(MessagesState):
    """
    State for the agent.
    """
    auth_urls: dict[str, str] | None = None

class LangGraphAgent(BaseAgent):
    """
    A streamlined LangGraph agent that handles tool calls using robust message
    extraction and integrates Arcade-based authorization when needed.
    """

    def __init__(self, model: str = "gpt-4o", tools: list[str] | None = None):
        super().__init__(model=model)
        self.prompt = ChatPromptTemplate.from_messages([("placeholder", "{messages}")])
        self.llm = ChatOpenAI(model=model)
        self.manager = ArcadeToolManager()
        self.tools = self.manager.get_tools(tools=tools, toolkits=TOOLKITS, langgraph=False)
        self.tool_node = ToolNode(self.tools)
        self.llm_with_tools = self.llm.bind_tools(self.tools, parallel_tool_calls=False)
        self.prompted_model = self.prompt | self.llm_with_tools

        self.setup_graph()

        # Cache tool descriptions to avoid repeated network calls
        self.cached_tool_descriptions = self.get_tool_descriptions()

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

    def get_system_prompt(self, user_timezone: str | None = None) -> str:
        """
        Return the enriched system prompt using cached tool descriptions.
        """
        return get_system_content(
            tool_descriptions=self.cached_tool_descriptions, user_timezone=user_timezone
        )

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
        Call the LLM with its tools using the full conversation context
        provided in state["messages"].
        """
        messages = state["messages"]
        # Generate response using the prompted model (which now uses full conversation history)
        response = self.prompted_model.invoke({"messages": messages})

        # Extract the assistant's reply and any tool calls
        return {"messages": [response]}

    def should_continue(self, state: AgentState, config: RunnableConfig) -> str:
        """
        Continue to the auth check if any message contains a tool call.
        """
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            if any(
                self.manager.requires_auth(tool_call["name"])
                for tool_call in last_message.tool_calls
            ):
                # Tools require authorization, check and make sure they are authorized
                return "check_auth"
            else:
                # Execute the tools, we don't need to check authorization
                return "tools"
        else:
            return END

    def check_auth(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        Check if the tool call(s) require user authorization.
        """
        user_id: str = config.get("configurable", {}).get("user_id")

        # create a dict of tools that require auth mapped to the url to authorize
        tools_to_auth: dict[str, str] = {}

        # get the tool calls from the last message
        for tool_call in state["messages"][-1].tool_calls:
            tool_name = tool_call["name"]

            # Check if the tool requires authorization
            if self.manager.requires_auth(tool_name):
                auth_response = self.manager.authorize(tool_name, user_id)

                # use map to deduplicate tools that require auth
                if auth_response.status != "completed" and tool_name not in tools_to_auth:
                    tools_to_auth[tool_name] = auth_response.url

        # Create formatted auth message if any tools require authorization
        if tools_to_auth:
            auth_message = self.__create_url_string_for_slack(tools_to_auth)
            return {"auth_urls": {user_id: auth_message}}

        # all tools authorized, return the state with no auth message
        # this will allow the agent to continue the conversation next time
        # TODO checkpoint and restart the graph
        return {"auth_urls": {user_id: None}}

    def authorize(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        Raise a NodeInterrupt if authorization is pending.
        """
        user_id = config.get("configurable", {}).get("user_id")

        # Check if auth_urls exists and has the user_id
        if "auth_urls" in state and user_id in state["auth_urls"]:
            auth_message = state["auth_urls"].get(user_id)

            # Only interrupt if auth_message is not None
            if auth_message is not None:
                raise NodeInterrupt(auth_message)

        # If we get here, either there's no auth_urls, no user_id in auth_urls,
        # or the auth_message is None (authorization complete)
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
        self.workflow.add_conditional_edges("agent", self.should_continue)
        self.workflow.add_edge("check_auth", "authorize")
        self.workflow.add_edge("authorize", "tools")
        self.workflow.add_edge("tools", "agent")

        # Compile the graph
        self.graph = self.workflow.compile()

    def __create_url_string_for_slack(self, tools_to_auth: dict[str, str]) -> str:
        """
        Create a string of tools that require auth and the urls to authorize them.

        This formats the auth urls for slack so they can be presented to the user
        in a readable and actionable way. Slack uses mrkdwn formatting for links
        in the format <url|text>.
        """

        # If no tools require auth, return empty string
        if not tools_to_auth:
            return ""

        # Format message based on number of tools requiring authorization
        if len(tools_to_auth) == 1:
            tool_name = next(iter(tools_to_auth.keys()))
            url = tools_to_auth[tool_name]
            auth_message = (
                f"Please authorize the *{tool_name}* tool by visiting:\n"
                f"<{url}|{tool_name} Tool>\n"
            )
        else:
            auth_message = "Please authorize access for the following tools:\n"
            for i, (tool_name, url) in enumerate(tools_to_auth.items(), 1):
                auth_message += f"{i}. *{tool_name}*: <{url}|{tool_name} Tool>\n"

        return auth_message
