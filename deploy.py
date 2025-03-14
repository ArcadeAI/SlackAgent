import os

import modal
from dotenv import load_dotenv
from modal import asgi_app

load_dotenv()

# Define your Modal stub
app = modal.App("SlackAgent")
vol = modal.Volume.from_name("archer", create_if_missing=True)

# Create a Modal image with necessary dependencies
image = (
    modal.Image.debian_slim()
    .add_local_dir("./dist", "/root/dist", copy=True)
    .pip_install("/root/dist/archer_slackbot-0.2.0-py3-none-any.whl")
)

# Define secrets to pass environment variables
secrets = modal.Secret.from_dict({
    "SLACK_BOT_TOKEN": os.environ["SLACK_BOT_TOKEN"],
    "SLACK_SIGNING_SECRET": os.environ["SLACK_SIGNING_SECRET"],
    "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
    "ARCADE_API_KEY": os.environ["ARCADE_API_KEY"],
    "FILE_STORAGE_BASE_DIR": "/data",
    "LANGSMITH_TRACING": os.environ["LANGSMITH_TRACING"],
    "LANGSMITH_ENDPOINT": os.environ["LANGSMITH_ENDPOINT"],
    "LANGSMITH_API_KEY": os.environ["LANGSMITH_API_KEY"],
    "LANGSMITH_PROJECT": os.environ["LANGSMITH_PROJECT"],
    "LOG_LEVEL": os.environ["LOG_LEVEL"],
})


@app.function(
    image=image, secrets=[secrets], volumes={"/data": vol}, keep_warm=1, allow_concurrent_inputs=100
)
@asgi_app()
def slack_agent():
    # Import here to ensure it happens inside the container
    from archer.server import create_fastapi_app

    return create_fastapi_app()
