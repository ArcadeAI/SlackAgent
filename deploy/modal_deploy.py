import os

import modal
from modal import App, Image, asgi_app

# Define your Modal stub
stub = App("archy")

# Create a Modal image with necessary dependencies
image = (
    Image.debian_slim()
    .copy_local_dir(".", "/root/")
    .pip_install_from_requirements("requirements.txt")
)

# Define secrets to pass environment variables
secrets = modal.Secret.from_dict({
    "SLACK_BOT_TOKEN": os.environ["SLACK_BOT_TOKEN"],
    "SLACK_SIGNING_SECRET": os.environ["SLACK_SIGNING_SECRET"],
    "ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"],
    "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
    "ARCADE_API_KEY": os.environ["ARCADE_API_KEY"],
})


@stub.function(image=image, secrets=[secrets])
@asgi_app()
def web_app():
    # Register your listeners
    from fastapi import FastAPI, Request
    from listeners import register_listeners
    from slack_bolt import App as Bolt
    from slack_bolt.adapter.fastapi import SlackRequestHandler

    # Initialize your Slack app
    slack_app = Bolt(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    )

    register_listeners(slack_app)

    # Create a SlackRequestHandler
    handler = SlackRequestHandler(slack_app)

    # Create a FastAPI app
    fastapi_app = FastAPI()

    # Define an endpoint to receive Slack requests
    @fastapi_app.post("/slack/events")
    async def endpoint(req: Request):
        return await handler.handle(req)

    return fastapi_app
