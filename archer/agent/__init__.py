import logging
from typing import List, Optional

from archer.agent.agent import ChatbotGraph
from archer.agent.constants import MODELS
from archer.agent.helpers import markdown_to_slack, redact_string, slack_to_markdown
from archer.prompts import DEFAULT_SYSTEM_CONTENT
from archer.storage.functions import get_user_state

logger = logging.getLogger(__name__)


def get_available_models():
    return MODELS

def get_agent(model: str = "gpt-4o"):
    return ChatbotGraph(model=model).get_graph()

def invoke_agent(
    user_id: str, prompt: str, context: Optional[List] = [], system_content=DEFAULT_SYSTEM_CONTENT
):
    if context:
        formatted_context = "\n".join([
            f"{msg['user']}: {slack_to_markdown(msg['text'])}" for msg in context
        ])
        full_prompt = f"Prompt: {prompt}\nContext: {formatted_context}"
    else:
        full_prompt = f"Prompt: {prompt}"
    try:
        user_settings = get_user_state(user_id)
        print(f"User settings: {user_settings}")

        state = {
            "messages": [
                {"role": "system", "content": DEFAULT_SYSTEM_CONTENT},
                {"role": "user", "content": full_prompt}
            ]
        }
        agent = get_agent(user_settings["model"])
        response = agent.invoke(state, config={"user_id": user_id})
        resp = response["messages"][-1].content
        resp = markdown_to_slack(redact_string(resp))
        return resp
    except Exception:
        logger.exception("Error generating response")
        raise

""" if __name__ == "__main__":
    print(invoke_agent("sam@arcade-ai.com", "Search Google for who sam partee is"))

 """
