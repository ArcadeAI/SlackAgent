from logging import Logger

from slack_bolt import Say
from slack_sdk import WebClient

from archer.agent import invoke_agent
from archer.agent.constants import DM_SYSTEM_CONTENT
from archer.listeners.utils import parse_conversation
from archer.prompts import DEFAULT_LOADING_TEXT


def direct_message_callback(client: WebClient, event: dict, logger: Logger, say: Say):
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts")
    user_id = event.get("user")
    text = event.get("text")

    logger.info(f"Channel ID: {channel_id}")
    logger.info(f"Thread TS: {thread_ts}")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Text: {text}")

    try:
        if event.get("channel_type") == "im":
            conversation_context = ""

            if thread_ts:  # Retrieves context to continue the conversation in a thread.
                conversation = client.conversations_replies(
                    channel=channel_id, limit=10, ts=thread_ts
                )["messages"]
                conversation_context = parse_conversation(conversation[:-1])
                logger.info(f"Conversation context: {conversation_context}")

            waiting_message = say(text=DEFAULT_LOADING_TEXT, thread_ts=thread_ts)
            response = invoke_agent(user_id, text, conversation_context, DM_SYSTEM_CONTENT)
            client.chat_update(channel=channel_id, ts=waiting_message["ts"], text=response)
    except Exception as e:
        logger.error(e)
        client.chat_update(
            channel=channel_id, ts=waiting_message["ts"], text=f"Received an error from Archy:\n{e}"
        )
