import logging

from langgraph.errors import NodeInterrupt

from archer.agent.agent import LangGraphAgent
from archer.agent.base import BaseAgent
from archer.agent.utils import markdown_to_slack, slack_to_markdown
from archer.defaults import MODELS, SYSTEM_CONTENT
from archer.storage.functions import get_user_state

logger = logging.getLogger(__name__)


def get_available_models() -> list[dict[str, str]]:  # TODO type this
    return MODELS


def get_agent(model: str = "gpt-4o") -> BaseAgent:
    logger.debug(f"Initializing Agent using model: {model}")
    return LangGraphAgent(model=model)


def invoke_agent(
    user_id: str,
    prompt: str,
    context: list[dict[str, str]] | None = None,
    system_content=SYSTEM_CONTENT,
):
    try:
        user_settings = get_user_state(user_id)
        logger.debug(f"User settings: {user_settings}")

        # Initialize agent using user settings
        agent = get_agent(user_settings["model"])

        # Use the enriched system prompt from the agent that includes tool descriptions and time info
        enriched_system_content = agent.get_system_prompt(
            user_timezone=user_settings.get("timezone")
        )

        if context:
            messages = [
                {"role": "system", "content": enriched_system_content},
                *context,
                {"role": "user", "content": slack_to_markdown(prompt)},
            ]
        else:
            messages = [
                {"role": "system", "content": enriched_system_content},
                {"role": "user", "content": slack_to_markdown(prompt)},
            ]

        state = {"messages": messages}

        try:
            response_state = agent.invoke(
                state,
                config={
                    "user_id": user_id,
                },
            )
        except NodeInterrupt as e:
            logger.info(f"Interrupt message: {e}")
            return e.value

        logger.info(f"Response state: {response_state}")

        # Check for auth_urls authorization
        if response_state.get("auth_urls"):
            auth_message = response_state["auth_urls"].get(user_id, None)
            if auth_message:
                return auth_message

        # Ensure 'messages' is in response_state and has content
        if response_state["messages"]:
            response_message = response_state["messages"][-1]
            if response_message.content:
                resp_content = response_message.content
                resp = markdown_to_slack(resp_content)
                return resp
            else:
                logger.error("Response message content is empty.")
                return "An error occurred: response content is empty."
        else:
            logger.error("No messages found in response state.")
            return "An error occurred: no response messages available."

    except Exception:
        logger.exception("Error generating response")
        return "An unexpected error occurred while processing your request."
