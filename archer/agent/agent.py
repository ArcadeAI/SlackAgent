import logging
import uuid

from langchain_arcade import ArcadeToolManager
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt

from archer.agent.base import BaseAgent
from archer.defaults import get_available_models, get_available_toolkits

logger = logging.getLogger(__name__)


class AgentState(MessagesState):
    """
    State for the agent.
    """

    auth_message: str | None = None
    resume_input: str | None = None


def handle_tool_error(state) -> dict:
    """
    Handle errors that occur during tool execution.

    Args:
        state: The current state with the error

    Returns:
        dict: Updated state with error messages
    """
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {error!r}\nPlease fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> ToolNode:
    """
    Create a tool node with error handling fallback.

    Args:
        tools: List of tools to include in the node

    Returns:
        ToolNode: A tool node with error handling
    """
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


class ReactAgent(BaseAgent):
    """
    A LangGraph agent that handles tool calls using robust message
    extraction and integrates Arcade-based authorization when needed.
    """

    def __init__(self, model: str = "gpt-4o", tools: list[str] | None = None):
        super().__init__(model=model)
        self.manager = ArcadeToolManager()
        self.tools = self.manager.get_tools(
            tools=tools, toolkits=get_available_toolkits(), langgraph=False
        )
        self.tool_node = create_tool_node_with_fallback(self.tools)
        # Initialize the chat model
        self.prompted_model = self._init_chat_model(model, self.tools)

        # Create a memory saver for the graph
        self.memory = MemorySaver()

        # Setup the graph after initializing all components
        self.setup_graph()

    def _init_chat_model(self, model: str, tools: list) -> BaseLanguageModel:
        """
        Initialize the chat model with the given model name.
        """
        models = get_available_models()
        record = models.get(model)
        if not record:
            raise ValueError(f"Model {model} not found")

        if record["provider"] == "OpenAI":
            llm = ChatOpenAI(model=model)
        else:
            raise ValueError(f"Provider {record['provider']} not supported")

        prompt = ChatPromptTemplate.from_messages([("placeholder", "{messages}")])
        llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=record["parallel_tool_calling"])
        prompted_model = prompt | llm_with_tools
        return prompted_model

    def invoke(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        Process the state through the graph and handle authentication interruptions.

        Args:
            state: The current agent state
            config: Configuration for the runnable

        Returns:
            AgentState: The updated state after processing
        """
        if "configurable" not in config:
            config["configurable"] = {}

        if "thread_id" not in config.get("configurable", {}):
            config["configurable"]["thread_id"] = str(uuid.uuid4())

        thread_id = config["configurable"]["thread_id"]
        logger.info(f"Using thread_id {thread_id} for graph execution")

        result = self.graph.invoke(state, config=config)
        return result

    def call_agent(self, state: AgentState, config: RunnableConfig) -> dict:
        """
        Call the LLM with its tools using the full conversation context
        provided in state["messages"].
        """
        messages = state.get("messages", [])
        response = self.prompted_model.invoke({"messages": messages})
        return {"messages": [response]}

    def should_continue(self, state: AgentState, config: RunnableConfig) -> str:
        """
        Determine the next node based on the presence of tool calls.

        Args:
            state: The current agent state
            config: Configuration for the runnable

        Returns:
            str: The name of the next node to execute
        """
        next_node = tools_condition(state)
        if next_node == END:
            return END

        # Pull tool calls from the last message in a safe way.
        messages = state.get("messages", [])
        last_msg = messages[-1] if messages else {}
        tool_calls = []
        if isinstance(last_msg, dict):
            tool_calls = last_msg.get("tool_calls", [])
        elif hasattr(last_msg, "tool_calls"):
            tool_calls = last_msg.tool_calls
        if any(
            (t.get("name") if isinstance(t, dict) else getattr(t, "name", None))
            and self.manager.requires_auth(
                t.get("name") if isinstance(t, dict) else getattr(t, "name", None)
            )
            for t in tool_calls
        ):
            return "check_auth"
        else:
            return "tools"

    def check_auth(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        Check if the tool call(s) require user authorization.

        Args:
            state: The current agent state
            config: Configuration for the runnable

        Returns:
            AgentState: Updated state or raises NodeInterrupt
        """
        user_id: str = config.get("configurable", {}).get("user_id")
        if not user_id:
            logger.warning("No user_id provided in config")
            return state

        tools_to_auth: dict[str, str] = {}
        messages = state.get("messages", [])
        if messages:
            last_msg = messages[-1]
            tool_calls = []
            if isinstance(last_msg, dict):
                tool_calls = last_msg.get("tool_calls", [])
            elif hasattr(last_msg, "tool_calls"):
                tool_calls = last_msg.tool_calls
            for tool_call in tool_calls:
                tool_name = (
                    tool_call.get("name")
                    if isinstance(tool_call, dict)
                    else getattr(tool_call, "name", None)
                )
                if tool_name and self.manager.requires_auth(tool_name):
                    auth_response = self.manager.authorize(tool_name, user_id)
                    if auth_response.status != "completed" and tool_name not in tools_to_auth:
                        tools_to_auth[tool_name] = auth_response.url

        if tools_to_auth:
            auth_message = self.__create_url_string_for_slack(tools_to_auth)

            # Set the auth_message in the state and trigger an interrupt
            logger.info(f"Authorization required for tools: {list(tools_to_auth.keys())}")
            return {"auth_message": auth_message}
        logger.info("All tools authorized, proceeding with execution")
        return {"auth_message": None}

    def auth_interrupt(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        Handle the authorization interruption.
        If auth_message is set in the state and no resume input has been provided,
        pause execution by triggering an interrupt with that value.
        If resume_input is present it means the graph is resuming from an earlier interrupt.
        """
        auth_message = state.get("auth_message")
        resume_input = state.get("resume_input")
        if auth_message and resume_input is None:
            # Trigger the interrupt to pause execution.
            interrupt(value=auth_message)
        elif resume_input is not None:
            # Clear the auth interrupt once a resume input has been provided.
            return {"auth_message": None, "resume_input": None}
        return state

    def setup_graph(self) -> None:
        """
        Build the conversation workflow graph.
        """
        self.workflow = StateGraph(AgentState)

        self.workflow.add_node("agent", self.call_agent)
        self.workflow.add_node("tools", self.tool_node)
        self.workflow.add_node("check_auth", self.check_auth)
        self.workflow.add_node("auth_interrupt", self.auth_interrupt)

        self.workflow.add_edge(START, "agent")
        self.workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "tools": "tools",
                "check_auth": "check_auth",
                END: END,
            },
        )

        def continue_after_check_auth(state: AgentState, config: RunnableConfig) -> str:
            return "auth_interrupt" if state.get("auth_message") else "tools"

        self.workflow.add_conditional_edges(
            "check_auth",
            continue_after_check_auth,
            {
                "auth_interrupt": "auth_interrupt",
                "tools": "tools",
            },
        )
        self.workflow.add_edge("tools", "agent")

        self.graph = self.workflow.compile(checkpointer=self.memory, debug=True)
        logger.info("Agent graph compiled successfully with memory checkpointing")

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
