import os

MODELS = {
	"gpt-4-turbo": {"name": "GPT-4 Turbo", "provider": "OpenAI", "max_tokens": 4096},
	"gpt-4": {"name": "GPT-4", "provider": "OpenAI", "max_tokens": 4096},
	"gpt-4o": {"name": "GPT-4o", "provider": "OpenAI", "max_tokens": 128000},
	"gpt-4o-mini": {"name": "GPT-4o mini", "provider": "OpenAI", "max_tokens": 128000},
}

def get_available_models():
    return MODELS

# Redaction patterns
#
REDACT_EMAIL_PATTERN = os.environ.get(
	"REDACT_EMAIL_PATTERN", r"\b[A-Za-z0-9.*%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
REDACT_PHONE_PATTERN = os.environ.get(
	"REDACT_PHONE_PATTERN", r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
REDACT_CREDIT_CARD_PATTERN = os.environ.get(
	"REDACT_CREDIT_CARD_PATTERN", r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"
)
REDACT_SSN_PATTERN = os.environ.get("REDACT_SSN_PATTERN", r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b")
# For REDACT_USER_DEFINED_PATTERN, the default will never match anything
REDACT_USER_DEFINED_PATTERN = os.environ.get("REDACT_USER_DEFINED_PATTERN", r"(?!)")
