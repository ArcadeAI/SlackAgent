import logging
import uuid
from dataclasses import dataclass

from langgraph.types import Command

from archer.agent.agent import ReactAgent
from archer.agent.base import BaseAgent
from archer.agent.utils import slack_to_markdown
from archer.defaults import get_system_prompt
from archer.storage.functions import get_user_state

logger = logging.getLogger(__name__)


# Module-level cache for agents. This ensures expensive initialization (like tool retrieval)
# is executed only once per model.
_agents: dict[str, BaseAgent] = {}


@dataclass
class AgentResponse:
    content: str | None = None
    auth_message: str | None = None
    thread_id: str | None = None


def get_agent(model: str = "gpt-4o") -> BaseAgent:
    """
    Create and cache a ReactAgent (which holds the tool definitions) for the given model.

    This ensures that we only perform the expensive calls to get tools once,
    and reuse the cached instance for subsequent invocations.
    """
    if model not in _agents:
        _agents[model] = ReactAgent(model=model)
    return _agents[model]


def build_state(system: str, prompt: str, context: list[dict[str, str]] | None = None) -> dict:
    """
    Construct the conversation state by building a list of messages:
      1. The first message is the system prompt.
      2. Any prior context messages (if provided) are appended.
      3. Finally, the user message is appended.
    """
    messages = [{"role": "system", "content": system}]
    if context:
        messages.extend(context)
    messages.append({"role": "user", "content": slack_to_markdown(prompt)})
    return {"messages": messages}


def invoke_agent(
    user_id: str,
    prompt: str,
    context: list[dict[str, str]] | None = None,
    thread_id: str | None = None,
    resume: bool = False,
) -> AgentResponse:
    """
    Invoke the agent with the given prompt and conversation context.
    If an authorization message is present in the computed state,
    the agent will raise an interrupt. The returned AgentResponse includes
    any auth_message.
    """
    try:
        user_settings = get_user_state(user_id)
        agent = get_agent(user_settings["model"])
        enriched_system_content = get_system_prompt(user_timezone=user_settings.get("timezone"))

        if not thread_id:
            thread_id = str(uuid.uuid4())

        if resume:
            command = Command(
                update={"resume_input": "yes"},
                resume="post-auth",
                goto="tools",
            )
            response_state = agent.graph.invoke(
                command, config={"configurable": {"user_id": user_id, "thread_id": thread_id}}
            )
        else:
            state = build_state(enriched_system_content, prompt, context)
            response_state = agent.invoke(
                state, config={"configurable": {"user_id": user_id, "thread_id": thread_id}}
            )
    except Exception:
        logger.exception("Error generating response")
        return AgentResponse(
            content="An unexpected error occurred while processing your request.",
            thread_id=thread_id,
        )
    else:
        last_message = response_state["messages"][-1]
        response = AgentResponse(
            content=last_message.content,
            auth_message=response_state.get("auth_message"),
            thread_id=thread_id,
        )
        logger.info(
            f"Agent response: auth_message={'present' if response.auth_message else 'absent'}, "
            f"thread_id={response.thread_id}, has_content={response.content is not None}"
        )
        return response
