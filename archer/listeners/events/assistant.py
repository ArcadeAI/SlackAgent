import json
import logging

from slack_bolt import Assistant, BoltContext, Say, SetStatus, SetSuggestedPrompts
from slack_sdk import WebClient

from archer.agent import invoke_agent
from archer.agent.utils import markdown_to_slack
from archer.defaults import DEFAULT_LOADING_TEXT, INITIAL_GREETING

# Shared assistant instance
assistant = Assistant()


# This listener is invoked when a human user opens an assistant thread
@assistant.thread_started
def start_assistant_thread(
    say: Say,
    set_suggested_prompts: SetSuggestedPrompts,
    logger: logging.Logger,
):
    try:
        say(INITIAL_GREETING)

        # Provide some suggested prompts to the user
        prompts: list[dict[str, str]] = [
            {
                "title": "Gmail Manager",
                "message": "Read my last 10 emails and tell me about them",
            },
            {
                "title": "Calendar Planner",
                "message": "What's on my calendar this week?",
            },
            {
                "title": "Developer Assistant",
                "message": "Tell me about any recently opened PRs in arcadeai/arcade-ai",
            },
        ]

        set_suggested_prompts(prompts=prompts)

    except Exception:
        logger.exception("Failed to handle an assistant_thread_started event")
        say(":warning: Looks like I had some trouble starting up. Please try again")


# This listener is invoked when the human user sends a reply in the assistant thread
@assistant.user_message
def respond_in_assistant_thread(
    payload: dict,
    logger: logging.Logger,
    context: BoltContext,
    set_status: SetStatus,
    say: Say,
    client: WebClient,
):
    try:
        # Extract user_id, user_message, and thread_id from the payload
        user_message = payload.get("text", "")
        user_id = payload.get("user")
        set_status(DEFAULT_LOADING_TEXT)

        # Generate a thread_id based on the channel and thread
        thread_id = f"{context.channel_id}:{context.thread_ts}"
        logger.info(f"Using thread_id: {thread_id} for conversation")

        # Retrieve conversation history from the thread
        replies = client.conversations_replies(
            channel=context.channel_id,
            ts=context.thread_ts,
            limit=10,
        )

        conversation_history = []
        for message in replies.get("messages", []):
            # Determine role based on presence of bot_id
            role = "user" if message.get("bot_id") is None else "assistant"
            conversation_history.append({"role": role, "content": message["text"]})

        # Invoke the agent with the user message and conversation history
        response = invoke_agent(
            user_id=user_id, prompt=user_message, context=conversation_history, thread_id=thread_id
        )

        # Log the response for debugging
        logger.info(f"Agent response type: {type(response)}")
        logger.info(f"Agent response auth_message: {response.auth_message}")
        logger.info(f"Agent response thread_id: {response.thread_id}")
        logger.info(f"Agent response has content: {response.content is not None}")

        # Check if the agent needs authorization
        if response.auth_message:
            # Format the auth message for Slack
            auth_message = response.auth_message
            logger.info(f"Auth message detected: {auth_message}")

            # Add instructions for the user
            auth_message += "\n\nAfter authorizing, click the button below to continue:"

            # Send message with a button that will provide a trigger_id when clicked
            say({
                "text": auth_message,
                "blocks": [
                    {"type": "section", "text": {"type": "mrkdwn", "text": auth_message}},
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Authorization Complete",
                                    "emoji": True,
                                },
                                "value": json.dumps({
                                    "user_id": user_id,
                                    "channel_id": context.channel_id,
                                    "thread_ts": context.thread_ts,
                                    "message": user_message,
                                    "thread_id": response.thread_id,
                                }),
                                "action_id": "auth_complete_button",
                            }
                        ],
                    },
                ],
            })

        else:
            # If no auth_message, just send the response content
            content = (
                markdown_to_slack(response.content) if hasattr(response, "content") else response
            )
            say(content)

    except Exception:
        logger.exception("Failed to handle a user message event")
        say(":warning: Looks like I had some trouble processing. Please try again.")
