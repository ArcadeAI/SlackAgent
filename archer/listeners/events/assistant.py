import json
import logging

from slack_bolt import Assistant, BoltContext, Say, SetStatus, SetSuggestedPrompts
from slack_sdk import WebClient

from archer.agent import invoke_agent
from archer.agent.utils import markdown_to_slack
from archer.defaults import DEFAULT_LOADING_TEXT
from archer.storage.functions import save_agent_state

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
        say("How can I help you?")

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
    except Exception as e:
        logger.exception("Failed to handle an assistant_thread_started event")
        say(f":warning: Something went wrong! ({e})")


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
        user_message = payload.get("text", "")
        user_id = payload.get("user")
        set_status(DEFAULT_LOADING_TEXT)

        # Retrieve conversation history from the thread
        replies = client.conversations_replies(
            channel=context.channel_id,
            ts=context.thread_ts,
            limit=15,
        )

        conversation_history = []
        for message in replies.get("messages", []):
            # Determine role based on presence of bot_id
            role = "assistant" if message.get("bot_id") else "user"
            conversation_history.append({"role": role, "content": message.get("text", "")})

        response = invoke_agent(user_id, user_message, context=conversation_history)

        # Check if the AgentResponse has an auth_message
        if hasattr(response, "auth_message") and response.auth_message is not None:
            # Save the agent state and get a unique ID
            state_id = save_agent_state(response.state) if hasattr(response, "state") else None

            # First, send the auth message to the user with a button to open the modal
            auth_message = response.auth_message

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
                                    "state_id": state_id,
                                }),
                                "action_id": "auth_complete_button",
                            }
                        ],
                    },
                ],
            })

            # Set status to waiting for authorization
            set_status("Waiting for user authorization...")

        else:
            # If no auth_message, just send the response content
            content = (
                markdown_to_slack(response.content) if hasattr(response, "content") else response
            )
            say(content)

    except Exception as e:
        logger.exception("Failed to handle a user message event")
        say(f":warning: Something went wrong! ({e})")
