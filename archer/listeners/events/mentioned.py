from logging import Logger
from typing import Any

from slack_bolt import Say
from slack_sdk import WebClient

from archer.agent import invoke_agent
from archer.defaults import (
    DEFAULT_LOADING_TEXT,
    DM_SYSTEM_CONTENT,
    MENTION_WITHOUT_TEXT,
)
from archer.env import BOT_NAME  # TODO: move to defaults
from archer.listeners.utils import parse_conversation


def app_mentioned_callback(
    ack: Any, client: WebClient, event: dict, logger: Logger, say: Say
):
    ack()
    logger.info(f"Event: {event}")
    if event.get("subtype") == "message_deleted":
        return
    try:
        channel_id = event.get("channel")
        thread_ts = event.get("thread_ts")
        user_id = event.get("user")
        text = event.get("text")

        logger.debug(f"Channel ID: {channel_id}")
        logger.debug(f"Thread TS: {thread_ts}")
        logger.debug(f"User ID: {user_id}")
        logger.debug(f"Text: {text}")

        if thread_ts:
            conversation = client.conversations_replies(
                channel=channel_id, ts=thread_ts, limit=10
            )["messages"]

            # get all but the most recent message (the user's current input)
            conversation_context = parse_conversation(conversation[:-1], user_id)
            logger.debug(f"Conversation context: {conversation_context}")
        else:
            # always respond in a thread.
            thread_ts = event["ts"]
            conversation_context = []

        if text:
            waiting_message = say(text=DEFAULT_LOADING_TEXT, thread_ts=thread_ts)
            logger.debug(f"Waiting message: {waiting_message}")
            response = invoke_agent(
                user_id, text, conversation_context, DM_SYSTEM_CONTENT
            )
            logger.debug(f"Response: {response}")
            client.chat_update(
                channel=channel_id, ts=waiting_message["ts"], text=response
            )
        else:
            client.chat_update(
                channel=channel_id, ts=waiting_message["ts"], text=MENTION_WITHOUT_TEXT
            )

    except Exception as e:
        logger.exception(e)
        client.chat_update(
            channel=channel_id,
            ts=waiting_message["ts"],
            text=f"Received an error from {BOT_NAME}:\n{e}",
        )
