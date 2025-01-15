import logging
from functools import lru_cache
from typing import Optional

from archer.agent.agent import LangGraphAgent
from archer.agent.base import BaseAgent
from archer.agent.utils import markdown_to_slack, redact_string, slack_to_markdown
from archer.defaults import DEFAULT_SYSTEM_CONTENT, MODELS
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
    context: Optional[list[dict[str, str]]] = None,
    system_content=DEFAULT_SYSTEM_CONTENT,
):
    if context:
        messages = [
            {"role": "system", "content": system_content},
            *context,
            {"role": "user", "content": slack_to_markdown(prompt)},
        ]
    else:
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": slack_to_markdown(prompt)},
        ]

    try:
        user_settings = get_user_state(user_id)
        logger.debug(f"User settings: {user_settings}")

        state = {"messages": messages}
        agent = get_agent(user_settings["model"])
        response_state = agent.invoke(
            state,
            config={
                "user_id": user_id,
            },
        )
        print(response_state)

        # Check for 'auth_url' in response_state
        if "auth_url" in response_state and response_state["auth_url"]:
            auth_url = response_state["auth_url"]
            logger.debug(f"Auth URL found: {auth_url}")
            return auth_url

        # Check for 'interrupt_message' in response_state
        if (
            "interrupt_message" in response_state
            and response_state["interrupt_message"]
        ):
            resp = response_state["interrupt_message"]
            return resp

        # Ensure 'messages' is in response_state and has content
        if "messages" in response_state and response_state["messages"]:
            response_message = response_state["messages"][-1]
            if response_message.content:
                resp_content = response_message.content
                resp = markdown_to_slack(redact_string(resp_content))
                return resp
            else:
                logger.error("Response message content is empty.")
                return "An error occurred: response content is empty."
        else:
            logger.error("No messages found in response state.")
            return "An error occurred: no response messages available."

    except Exception as e:
        logger.exception(f"Error generating response: {e}")
        return "An unexpected error occurred while processing your request."
