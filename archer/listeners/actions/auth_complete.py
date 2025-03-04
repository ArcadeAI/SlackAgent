import json
import logging
import uuid
from typing import Any

from slack_bolt import Ack, BoltContext
from slack_sdk import WebClient

from archer.agent import invoke_agent
from archer.agent.utils import markdown_to_slack


def handle_auth_complete(
    ack: Ack,
    body: dict[str, Any],
    logger: logging.Logger,
    client: WebClient,
    context: BoltContext,
):
    # Acknowledge the view submission immediately.
    ack()

    try:
        # Extract metadata from the view.
        metadata = json.loads(body["view"]["private_metadata"])
        user_id = metadata["user_id"]
        channel_id = metadata["channel_id"]
        thread_ts = metadata["thread_ts"]
        user_message = metadata["message"]
        thread_id = metadata.get("thread_id", str(uuid.uuid4()))

        # Post a temporary loading message.
        temp_message = client.chat_postMessage(
            channel=channel_id,
            text="Resuming after authorization...",
            thread_ts=thread_ts,
            as_user=True,
        )

        # Retrieve the saved state if available
        conversation_history = []

        # Retrieve conversation history from the thread
        replies = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=10,
        )
        for message in replies.get("messages", []):
            # Determine role based on presence of bot_id
            role = "user" if message.get("bot_id") is None else "assistant"
            conversation_history.append({"role": role, "content": message.get("text", "")})

        logger.info(f"Resuming agent for user {user_id} with thread_id: {thread_id}")

        # Re-invoke the agent with the same prompt and restored state
        response = invoke_agent(
            user_id=user_id,
            prompt=user_message,
            context=conversation_history,
            thread_id=thread_id,
            resume=True,
        )

        # Delete the temporary loading message.
        try:
            client.chat_delete(channel=channel_id, ts=temp_message["ts"])
        except Exception as e:
            logger.warning(f"Could not delete loading message: {e}")

        # Send the response to the thread as the assistant
        content = response.content if hasattr(response, "content") else response

        # Check if content is empty (which happens when the agent only makes tool calls)
        if content:
            client.chat_postMessage(
                channel=channel_id,
                text=markdown_to_slack(content),
                thread_ts=thread_ts,
                as_user=True,  # This maintains the assistant's identity
            )

    except Exception as e:
        logger.exception("Error handling auth completion")
        client.chat_postMessage(
            channel=channel_id,
            text=f":warning: Something went wrong after the authorization: {e!s}",
            thread_ts=thread_ts,
            as_user=True,  # Maintain assistant identity even for errors
        )
