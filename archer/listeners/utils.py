import logging
from typing import List, Optional

from slack_sdk.web.slack_response import SlackResponse

logger = logging.getLogger(__name__)

"""
TODO: Account for more edge cases in channels and multi-text or multi-user messages
"""


def parse_conversation(
    conversation: SlackResponse, user_id: str
) -> Optional[List[dict]]:
    parsed = []
    try:
        for message in conversation:
            msg_user_id = message["user"]
            role = "user" if msg_user_id == user_id else "assistant"
            text = message["text"]
            parsed.append({"role": role, "content": text})
        return parsed
    except Exception as e:
        logger.error(e)
    return None
