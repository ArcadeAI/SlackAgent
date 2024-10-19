
import os

import modal
from modal import asgi_app

# Define your Modal stub
app = modal.App("Archer")
vol = modal.Volume.from_name("archer", create_if_missing=True)
# Create a Modal image with necessary dependencies
image = (
    modal.Image.debian_slim()
    .copy_local_dir("./dist", "/root/dist")
    .pip_install("/root/dist/archer_slackbot-0.1.0-py3-none-any.whl")
)

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
    from archer.server import fastapi_app
    return fastapi_app
