from archer.env import SHORTEN_TOOL_DESCRIPTIONS
from archer.utils import get_formatted_times, get_tool_section

MENTION_WITHOUT_TEXT = """
Hi there! You didn't provide a message with your mention.
    Mention me again in this thread so that I can help you out!
"""

DEFAULT_LOADING_TEXT = "working on it..."

SYSTEM_CONTENT = """
You are a versatile AI assistant named Archer. You were created by Arcade AI.
Provide concise, relevant assistance tailored to each request from users.

You have access to a variety of tools to help you with your tasks. These
tools are listed below along with descriptions you can use to help you call
the tools when needed to respond to the user and correctly call each tool.

{tools_section}

When appropriate, you can call multiple tools in parallel to efficiently gather information.
For example, you might search for information while also checking a user's calendar.

Note that context is sent in order of the most recent message last.
Do not respond to messages in the context, as they have already been answered.
Be professional and friendly.
Don't ask for clarification unless absolutely necessary.
Don't ask questions in your response.
Don't use user names in your response.
"""


def get_system_content(
    tool_descriptions: dict[str, str] | None = None,
    user_timezone: str | None = None,
    shorten_descriptions: bool = SHORTEN_TOOL_DESCRIPTIONS,
) -> str:
    tools_section = get_tool_section(tool_descriptions, shorten_descriptions)

    # Get formatted times for all major time zones
    current_times = get_formatted_times(user_timezone)

    return f"""
{SYSTEM_CONTENT.format(tools_section=tools_section)}

This is a private thread between you and user.

When discussing times or scheduling, be aware of the user's potential time zone
and provide relevant time conversions when appropriate.

Current times around the world:
{current_times}

Consider using the appropriate tool to provide more accurate and helpful responses.
"""


TOOLKITS = ["github", "google", "x", "search"]

MODELS = {
    "o3-mini": {"name": "o3-mini", "provider": "OpenAI", "max_tokens": 200000},
    "gpt-4o": {"name": "GPT-4o", "provider": "OpenAI", "max_tokens": 128000},
    "gpt-4o-mini": {"name": "GPT-4o mini", "provider": "OpenAI", "max_tokens": 128000},
}

def get_available_models() -> dict[str, dict[str, str | int]]:
    return MODELS

def get_available_toolkits() -> list[str]:
    return TOOLKITS
