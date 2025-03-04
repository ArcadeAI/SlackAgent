import json
import logging
from typing import Any

from slack_bolt import Ack, BoltContext
from slack_sdk import WebClient


def handle_auth_complete_button(
    ack: Ack,
    body: dict[str, Any],
    logger: logging.Logger,
    client: WebClient,
    context: BoltContext,
):
    # Acknowledge the button click right away
    ack()

    try:
        # Extract the value from the button
        value = json.loads(body["actions"][0]["value"])
        user_id = value["user_id"]
        channel_id = value["channel_id"]
        thread_ts = value["thread_ts"]
        user_message = value["message"]
        thread_id = value.get("thread_id")

        logger.info(f"Auth complete button clicked: thread_id={thread_id} user_id={user_id}")

        # Now we have a valid trigger_id from the button click
        trigger_id = body["trigger_id"]

        # Open the modal with the authorization complete button
        client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "Authorization Check",
                    "emoji": True,
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Yes, I'm done",
                    "emoji": True,
                },
                "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
                "callback_id": "auth_complete",
                "private_metadata": json.dumps({
                    "user_id": user_id,
                    "channel_id": channel_id,
                    "thread_ts": thread_ts,
                    "message": user_message,
                    "thread_id": thread_id,
                }),
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "If you've authorized the tool, click the button below.",
                        },
                    }
                ],
            },
        )
    except Exception as e:
        logger.exception("Failed to open modal view")
        client.chat_postMessage(
            channel=channel_id,
            text=f":warning: Could not open authorization dialog: {e!s}",
            thread_ts=thread_ts,
            as_user=True,
        )
