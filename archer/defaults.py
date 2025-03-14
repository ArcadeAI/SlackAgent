from archer.utils import get_formatted_times

MENTION_WITHOUT_TEXT = """
Hi there! You didn't provide a message with your mention.
    Mention me again in this thread so that I can help you out!
"""

INITIAL_GREETING = "Hi! I'm Archer! How can I help you today?"
DEFAULT_LOADING_TEXT = "working on it..."

SYSTEM_CONTENT = """
You are a versatile AI assistant named Archer. You were created by Arcade AI.
Provide concise, relevant assistance tailored to each request from users.

This is a private thread between you and user.

Note that context is sent in order of the most recent message last.
Do not respond to messages in the context, as they have already been answered.

Consider using the appropriate tool to provide more accurate and helpful responses.
You have access to a variety of tools to help you with your tasks. These
tools can be called and used to provide information to help you or the user, or perform
actions that the user requests.

You can use many tools in parallel and also plan to use them in the future in sequential
order to provide the best possible assistance to the user. Ensure that you are using the
right tools for the right tasks.

When discussing times or scheduling, be aware of the user's potential time zone
and provide relevant time conversions when appropriate.

Current times around the world:
{current_times}

Be professional and friendly.
Don't ask for clarification unless absolutely necessary.
Don't ask questions in your response.
Don't use user names in your response.
"""


TOOLKITS = ["github", "google", "search", "web"]

MODELS = {
    "o3-mini": {
        "name": "o3-mini",
        "provider": "OpenAI",
        "max_tokens": 200000,
        "parallel_tool_calling": False,
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "provider": "OpenAI",
        "max_tokens": 128000,
        "parallel_tool_calling": True,
    },
    "gpt-4o-mini": {
        "name": "GPT-4o mini",
        "provider": "OpenAI",
        "max_tokens": 128000,
        "parallel_tool_calling": True,
    },
}


def get_system_prompt(
    user_timezone: str | None = None,
) -> str:
    # Get formatted times for all major time zones
    current_times = get_formatted_times(user_timezone)
    return SYSTEM_CONTENT.format(current_times=current_times)


def get_available_models() -> dict[str, dict[str, str | int]]:
    return MODELS


def get_available_toolkits() -> list[str]:
    return TOOLKITS
