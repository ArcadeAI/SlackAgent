from logging import Logger

from slack_bolt import Say
from slack_sdk import WebClient

from archer.agent import invoke_agent
from archer.listeners.utils import parse_conversation
from archer.prompts import DEFAULT_LOADING_TEXT, MENTION_WITHOUT_TEXT


def app_mentioned_callback(client: WebClient, event: dict, logger: Logger, say: Say):
	try:
		channel_id = event.get("channel")
		thread_ts = event.get("thread_ts")
		user_id = event.get("user")
		text = event.get("text")

		logger.info(f"Channel ID: {channel_id}")
		logger.info(f"Thread TS: {thread_ts}")
		logger.info(f"User ID: {user_id}")
		logger.info(f"Text: {text}")

		if thread_ts:
				conversation = client.conversations_replies(channel=channel_id, ts=thread_ts, limit=10)[
						"messages"
				]
		else:
				conversation = client.conversations_history(channel=channel_id, limit=10)["messages"]
				thread_ts = event["ts"]

		conversation_context = parse_conversation(conversation[:-1])

		logger.info(f"Conversation context: {conversation_context}")

		if text:
				waiting_message = say(text=DEFAULT_LOADING_TEXT, thread_ts=thread_ts)
				logger.info(f"Waiting message: {waiting_message}")
				response = invoke_agent(user_id, text, conversation_context)
				logger.info(f"Response: {response}")
				client.chat_update(channel=channel_id, ts=waiting_message["ts"], text=response)
		else:
				response = MENTION_WITHOUT_TEXT
				client.chat_update(channel=channel_id, ts=waiting_message["ts"], text=response)

	except Exception as e:
		logger.exception(e)
		client.chat_update(
				channel=channel_id, ts=waiting_message["ts"], text=f"Received an error from Archy:\n{e}"
		)
