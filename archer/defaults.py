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
Note that context is sent in order of the most recent message last.
Do not respond to messages in the context, as they have already been answered.
Be professional and friendly.
Don't ask for clarification unless absolutely necessary.
Don't ask questions in your response.
Don't use user names in your response.
"""

DM_SYSTEM_CONTENT = f"""
This is a private DM between you and user.

{DEFAULT_SYSTEM_CONTENT}
Todays date is {datetime.now().strftime("%Y-%m-%d")}
"""

MODELS = {
    "gpt-4-turbo": {"name": "GPT-4 Turbo", "provider": "OpenAI", "max_tokens": 4096},
    "gpt-4": {"name": "GPT-4", "provider": "OpenAI", "max_tokens": 4096},
    "gpt-4o": {"name": "GPT-4o", "provider": "OpenAI", "max_tokens": 128000},
    "gpt-4o-mini": {"name": "GPT-4o mini", "provider": "OpenAI", "max_tokens": 128000},
}


def get_available_models():
    return MODELS
