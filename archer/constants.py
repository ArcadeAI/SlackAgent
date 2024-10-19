import os

# High level constants

BOT_NAME = "Archer"

REDACTION_ENABLED = bool(os.environ.get("REDACTION_ENABLED", False))

ARCADE_API_KEY = os.environ.get("ARCADE_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
