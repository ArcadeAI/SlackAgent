import os

import modal
from dotenv import load_dotenv
from modal import asgi_app

load_dotenv()

# Define your Modal stub
app = modal.App("Archer")
vol = modal.Volume.from_name("archer", create_if_missing=True)
# Create a Modal image with necessary dependencies
image = (
    modal.Image.debian_slim()
    .copy_local_dir("./dist", "/root/dist")
    .pip_install("/root/dist/archer_slackbot-0.2.0-py3-none-any.whl")
    .pip_install("langchain-arcade", "langchain-openai", "langchain")
)

with image.imports():
    from archer.server import create_fastapi_app

    fastapi_app = create_fastapi_app()

# Define secrets to pass environment variables
secrets = modal.Secret.from_dict({
    "SLACK_BOT_TOKEN": os.environ["SLACK_BOT_TOKEN"],
    "SLACK_SIGNING_SECRET": os.environ["SLACK_SIGNING_SECRET"],
    "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
    "ARCADE_API_KEY": os.environ["ARCADE_API_KEY"],
    "FILE_STORAGE_BASE_DIR": "/data",
})


@app.function(image=image, secrets=[secrets], volumes={"/data": vol})
@asgi_app()
def web_app():
    return fastapi_app
