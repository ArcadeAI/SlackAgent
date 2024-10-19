import logging
from typing import List, Optional

from slack_sdk.web.slack_response import SlackResponse

logger = logging.getLogger(__name__)

"""
Parses a conversation history, excluding messages from the bot,
and formats it as a string with user IDs and their messages.
Used in `app_mentioned_callback`, `dm_sent_callback`,
and `handle_summary_function_callback`."""


def parse_conversation(conversation: SlackResponse) -> Optional[List[dict]]:
    parsed = []
    try:
        for message in conversation:
            user = message["user"]
            text = message["text"]
            parsed.append({"user": user, "text": text})
        return parsed
    except Exception as e:
        logger.error(e)
        return None
