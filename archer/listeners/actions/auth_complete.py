import json
import logging
from typing import Any

from slack_bolt import Ack, BoltContext
from slack_sdk import WebClient

from archer.agent import invoke_agent
from archer.agent.utils import markdown_to_slack
from archer.storage.functions import get_agent_state


def handle_auth_complete(
    ack: Ack,
    body: dict[str, Any],
    logger: logging.Logger,
    client: WebClient,
    context: BoltContext,
):
    # Acknowledge the view submission right away
    ack()

    try:
        # Extract metadata from the view
        metadata = json.loads(body["view"]["private_metadata"])
        user_id = metadata["user_id"]
        channel_id = metadata["channel_id"]
        thread_ts = metadata["thread_ts"]
        user_message = metadata["message"]
        state_id = metadata.get("state_id")

        # Post a temporary loading message as the assistant
        temp_message = client.chat_postMessage(
            channel=channel_id,
            text="Resuming... :hourglass_flowing_sand:",
            thread_ts=thread_ts,
            as_user=True,  # Post as the bot user
        )

        # Retrieve the saved state if available
        conversation_history = []
        state = None
        if state_id:
            try:
                state = get_agent_state(state_id)
                logger.info(f"Retrieved agent state with ID: {state_id}")
            except Exception as e:
                logger.warning(f"Could not retrieve agent state: {e}")
                state = None

        if state is None:
            # Retrieve conversation history from the thread
            replies = client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=15,
            )
            for message in replies.get("messages", []):
                # Determine role based on presence of bot_id
                role = "assistant" if message.get("bot_id") else "user"
                conversation_history.append({"role": role, "content": message.get("text", "")})

        # Invoke the agent again with the same message but now with authorization
        response = invoke_agent(user_id, user_message, context=conversation_history, state=state)

        # Delete the temporary loading message
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
        else:
            logger.info(f"Agent response was empty: {response}")

    except Exception as e:
        logger.exception("Error handling auth completion")
        client.chat_postMessage(
            channel=channel_id,
            text=f":warning: Something went wrong after the authorization: {e!s}",
            thread_ts=thread_ts,
            as_user=True,  # Maintain assistant identity even for errors
        )
