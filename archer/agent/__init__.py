import logging
from typing import List, Optional

from state_store.get_user_state import get_user_state

from archer.agent.constants import MODELS
from archer.agent.utils import markdown_to_slack, redact_string, slack_to_markdown
from archer.prompts import DEFAULT_SYSTEM_CONTENT

logger = logging.getLogger(__name__)


def get_available_models():
    return MODELS

def _get_provider(provider_name: str):
    if provider_name.lower() == "openai":
        return OpenAI_API()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def invoke_agent(
    user_id: str, prompt: str, context: Optional[List] = [], system_content=DEFAULT_SYSTEM_CONTENT
):
    formatted_context = "\n".join([
        f"{msg['user']}: {slack_to_markdown(msg['text'])}" for msg in context
    ])
    full_prompt = f"Prompt: {prompt}\nContext: {formatted_context}"
    try:
        provider_name, model_name = get_user_state(user_id, False)
        provider = _get_provider(provider_name)
        provider.set_model(model_name)
        response = provider.generate_response(full_prompt, system_content, user_id)
        return markdown_to_slack(redact_string(response))
    except Exception:
        logger.exception("Error generating response")
        raise

