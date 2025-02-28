import logging
from dataclasses import dataclass
from typing import Any

from archer.agent.agent import LangGraphAgent
from archer.agent.base import BaseAgent
from archer.agent.utils import slack_to_markdown
from archer.defaults import MODELS, SYSTEM_CONTENT
from archer.storage.functions import get_user_state

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    content: str | None = None
    auth_message: str | None = None
    state: dict[str, Any] | None = None


def get_available_models() -> list[dict[str, str]]:
    return MODELS


def get_agent(model: str = "gpt-4o") -> BaseAgent:
    return LangGraphAgent(model=model)


def invoke_agent(
    user_id: str,
    prompt: str,
    context: list[dict[str, str]] | None = None,
    system_content=SYSTEM_CONTENT,
    state: dict | None = None,
) -> AgentResponse:
    try:
        user_settings = get_user_state(user_id)
        logger.debug(f"User settings: {user_settings}")

        # Initialize agent using user settings
        agent = get_agent(user_settings["model"])

        # Use the enriched system prompt from the agent that includes tool descriptions and time info
        enriched_system_content = agent.get_system_prompt(
            user_timezone=user_settings.get("timezone")
        )

        if state is None:
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
        else:
            # Ensure the state has the right structure
            if "messages" not in state:
                state["messages"] = []

            # Make sure auth_urls is cleared or set to None values
            if "auth_urls" in state:
                for key in state["auth_urls"]:
                    state["auth_urls"][key] = None

        response_state = agent.invoke(
            state,
            config={
                "user_id": user_id,
            },
        )

        # Create AgentResponse with the full state for potential resumption
        response = AgentResponse(
            content=response_state["messages"][-1].content
            if response_state.get("messages")
            else "",
            auth_message=response_state.get("auth_urls", {}).get(user_id, None),
            state=response_state,  # Include the full state for resumption
        )

        logger.info(f"Response state: {response_state}")
        return response

    except Exception:
        logger.exception("Error generating response")
        return AgentResponse(content="An unexpected error occurred while processing your request.")
