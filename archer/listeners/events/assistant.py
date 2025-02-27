import logging

from slack_bolt import Assistant, BoltContext, Say, SetStatus, SetSuggestedPrompts
from slack_sdk import WebClient

from archer.agent import invoke_agent
from archer.defaults import DEFAULT_LOADING_TEXT

# Shared assistant instance
assistant = Assistant()


def register_assistant_listeners(app):
    """Register assistant middleware on the Slack app."""
    app.use(assistant.middleware)


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
            oldest=context.thread_ts,
            limit=50,
        )

        conversation_history = []
        for message in replies.get("messages", []):
            # Determine role based on presence of bot_id
            role = "assistant" if message.get("bot_id") else "user"
            conversation_history.append({"role": role, "content": message.get("text", "")})

        # Pass the full conversation history as context to the agent
        response = invoke_agent(user_id, user_message, context=conversation_history)
        say(response)

    except Exception as e:
        logger.exception("Failed to handle a user message event")
        say(f":warning: Something went wrong! ({e})")
