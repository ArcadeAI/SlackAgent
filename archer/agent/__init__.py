import logging
from typing import Optional

from archer.agent.agent import LangGraphAgent
from archer.agent.utils import markdown_to_slack, redact_string, slack_to_markdown
from archer.defaults import DEFAULT_SYSTEM_CONTENT, MODELS
from archer.storage.functions import get_user_state

logger = logging.getLogger(__name__)


def get_available_models():
    return MODELS

def get_agent(model: str = "gpt-4o"):
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
            }
        )
        if 'interrupt_message' in response_state:
            resp = markdown_to_slack(redact_string(response_state['interrupt_message']))
            return resp

        response_message = response_state["messages"][-1]
        resp_content = response_message.content
        resp = markdown_to_slack(redact_string(resp_content))
        return resp
    except Exception:
        logger.exception("Error generating response")
        raise

