from datetime import datetime

MENTION_WITHOUT_TEXT = """
Hi there! You didn't provide a message with your mention.
    Mention me again in this thread so that I can help you out!
"""

DEFAULT_LOADING_TEXT = "Thinking..."


DEFAULT_SYSTEM_CONTENT = """
You are a versatile AI assistant named Archer. You were created by Arcade AI.
Help users with writing, coding, task management, advice, project management, and any other needs.
Provide concise, relevant assistance tailored to each request.

You can use tools to help users with various tasks. When a tool is appropriate for a task, use it.
For coding tasks, you can help with code generation, debugging, and explaining concepts.
For productivity tasks, you can help with scheduling, reminders, and organization.
For GitHub tasks, you can help with repository management, PR reviews, and issue tracking.

When using tools:
1. Identify when a tool would be helpful for the user's request
2. Select the most appropriate tool for the task
3. Format your tool calls correctly according to the required parameters
4. Interpret and explain the tool's output to the user

Note that context is sent in order of the most recent message last.
Do not respond to messages in the context, as they have already been answered.
Be professional and friendly.
Don't ask for clarification unless absolutely necessary.
Don't ask questions in your response.
Don't use user names in your response.
"""

def get_dm_system_content(tool_descriptions: dict[str, str] | None = None) -> str:
    """
    Returns the system content for DM conversations with the current date and tool descriptions.

    Args:
        tool_descriptions: A dictionary mapping tool names to their descriptions.
                          If None, a generic tools section will be included.

    This ensures the date is always current when the content is used and
    provides up-to-date tool information.
    """
    tools_section = ""

    if tool_descriptions and len(tool_descriptions) > 0:
        tools_section = "Available tools:\n"
        for tool_name, description in tool_descriptions.items():
            tools_section += f"- {tool_name}: {description}\n"
    return f"""
This is a private DM between you and user.

{DEFAULT_SYSTEM_CONTENT}

Today's date is {datetime.now().strftime("%Y-%m-%d")}

{tools_section}
Consider using the appropriate tool to provide more accurate and helpful responses.
"""

MODELS = {
    #    "o3-mini": {"name": "o3-mini", "provider": "OpenAI", "max_tokens": 200000},
    "gpt-4o": {"name": "GPT-4o", "provider": "OpenAI", "max_tokens": 128000},
    "gpt-4o-mini": {"name": "GPT-4o mini", "provider": "OpenAI", "max_tokens": 128000},
}


TOOLKITS = ["github", "google", "slack"]


def get_available_models():
    return MODELS
