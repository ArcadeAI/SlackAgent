from archer.env import SHORTEN_TOOL_DESCRIPTIONS
from archer.utils import get_formatted_times

MENTION_WITHOUT_TEXT = """
Hi there! You didn't provide a message with your mention.
    Mention me again in this thread so that I can help you out!
"""

DEFAULT_LOADING_TEXT = "Thinking..."


DEFAULT_SYSTEM_CONTENT = """
You are a versatile AI assistant named Archer. You were created by Arcade AI.
Provide concise, relevant assistance tailored to each request from users.

You have access to a variety of tools to help you with your tasks. These
tools are listed below along with descriptions you can use to help you call
the tools when needed to respond to the user and correctly call each tool.

{tools_section}

Note that context is sent in order of the most recent message last.
Do not respond to messages in the context, as they have already been answered.
Be professional and friendly.
Don't ask for clarification unless absolutely necessary.
Don't ask questions in your response.
Don't use user names in your response.
"""


def get_dm_system_content(
    tool_descriptions: dict[str, str] | None = None,
    user_timezone: str | None = None,
    shorten_descriptions: bool = SHORTEN_TOOL_DESCRIPTIONS,
) -> str:
    """
    Returns the system content for DM conversations with the current date and tool descriptions.

    Args:
        tool_descriptions: A dictionary mapping tool names to their descriptions.
                          If None, a generic tools section will be included.
        user_timezone: The timezone of the user.
        shorten_descriptions: Whether to shorten the tool descriptions to 100 characters.

    This ensures the date is always current when the content is used and
    provides up-to-date tool information.
    """
    tools_section = ""

    if tool_descriptions and len(tool_descriptions) > 0:
        tools_section = "Available tools:\n"
        for tool_name, description in tool_descriptions.items():
            # Shorten description if requested
            if shorten_descriptions and len(description) > 100:
                short_desc = description[:97] + "..."
                tools_section += f"- {tool_name}: {short_desc}"
            else:
                # Format description with proper spacing for LLM readability
                tools_section += f"- {tool_name}: {description}\n"

    # Get formatted times for all major time zones
    current_times = get_formatted_times(user_timezone)

    return f"""
{DEFAULT_SYSTEM_CONTENT.format(tools_section=tools_section)}

This is a private DM between you and user.

When discussing times or scheduling, be aware of the user's potential time zone
and provide relevant time conversions when appropriate.

Current times around the world:
{current_times}

Consider using the appropriate tool to provide more accurate and helpful responses.
"""


TOOLKITS = ["github", "google", "slack"]

MODELS = {
    "o3-mini": {"name": "o3-mini", "provider": "OpenAI", "max_tokens": 200000},
    "gpt-4o": {"name": "GPT-4o", "provider": "OpenAI", "max_tokens": 128000},
    "gpt-4o-mini": {"name": "GPT-4o mini", "provider": "OpenAI", "max_tokens": 128000},
}


def get_available_models() -> dict[str, dict[str, str | int]]:
    return MODELS


def get_available_toolkits() -> list[str]:
    return TOOLKITS
