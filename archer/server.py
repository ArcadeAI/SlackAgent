import logging
from typing import Callable

from fastapi import FastAPI, Request

#from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
#from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_bolt.app import App
from slack_bolt.response import BoltResponse

from archer.constants import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
from archer.listeners import register_listeners

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_slack_app():
    slack_app = App(
        name="Archer",
        logger=logger,
        signing_secret=SLACK_SIGNING_SECRET,
        token=SLACK_BOT_TOKEN
    )

    @slack_app.middleware
    def log_request(logger: logging.Logger, body: dict, next: Callable[[], BoltResponse]) -> BoltResponse:
        logger.info(body)
        return next()
    register_listeners(slack_app)
    return slack_app

slack_app = create_slack_app()
# register all the events, actions, commands, and function listeners
fastapi_handler = SlackRequestHandler(slack_app)
fastapi_app = FastAPI()

# Define an endpoint to receive Slack requests
@fastapi_app.post("/slack/events")
async def endpoint(req: Request):
    return await fastapi_handler.handle(req)
