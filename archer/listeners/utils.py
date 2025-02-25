import logging

from slack_sdk.web.slack_response import SlackResponse

logger = logging.getLogger(__name__)

"""
TODO: Account for more edge cases in channels and multi-text or multi-user messages
"""


def parse_conversation(conversation: SlackResponse, user_id: str) -> list[dict] | None:
    parsed = []
    try:
        for message in conversation:
            msg_user_id = message["user"]
            role = "user" if msg_user_id == user_id else "assistant"
            text = message["text"]
            parsed.append({"role": role, "content": text})
    except Exception:
        logger.exception("Error parsing conversation")
        return None
    else:
        return parsed
