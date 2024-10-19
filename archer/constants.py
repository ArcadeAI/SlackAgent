import os

# High level constants

BOT_NAME = "Archer"
STORAGE_TYPE = os.environ.get("STORAGE_TYPE", "file")
FILE_STORAGE_BASE_DIR = os.environ.get("FILE_STORAGE_BASE_DIR", "/tmp/")

REDACTION_ENABLED = bool(os.environ.get("REDACTION_ENABLED", False))

ARCADE_API_KEY = os.environ.get("ARCADE_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")
