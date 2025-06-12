import logging
import os
import sys
import threading
from collections import deque
from collections.abc import Callable

from fastapi import FastAPI, Request
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_bolt.app import App
from slack_bolt.response import BoltResponse

from archer.env import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
from archer.listeners import register_listeners

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Thread-safe deque to store processed event IDs
processed_events: deque[str] = deque(maxlen=1000)
event_lock: threading.Lock = threading.Lock()


def create_slack_app() -> App:
    slack_app = App(
        name="Archer",
        logger=logger,
        signing_secret=SLACK_SIGNING_SECRET,
        token=SLACK_BOT_TOKEN,
    )

    @slack_app.middleware
    def deduplicate_events(
        req: Request,
        resp: BoltResponse,
        next: Callable[[], BoltResponse],  # noqa: A002
    ) -> BoltResponse:
        event_id = req.body.get("event_id")
        event_type = req.body.get("event", {}).get("type")

        if event_type in ["message", "app_mention", "assistant"] and event_id:
            with event_lock:
                if event_id in processed_events:
                    logger.info(f"Duplicate event detected: {event_id}, skipping processing.")
                    return BoltResponse(status=200)
                else:
                    processed_events.append(event_id)

        return next()

    register_listeners(slack_app)
    return slack_app


def create_fastapi_app() -> FastAPI:
    slack_app = create_slack_app()
    fastapi_handler = SlackRequestHandler(slack_app)
    fastapi_app = FastAPI()

    # Define an endpoint to receive Slack requests
    @fastapi_app.post("/slack/events")
    async def endpoint(req: Request):
        # Log as much detail as possible.
        logger.debug(
            f"\nReceived {req.method} request\n"
            f"URL path: {req.url.path}\n"
            f"Query string: {req.url.query}\n"
            f"Headers: {dict(req.headers)}\n"
        )
        
        # Handle Slack URL verification
        body = await req.json()
        if body.get("type") == "url_verification":
            return {"challenge": body["challenge"]}
            
        return await fastapi_handler.handle(req)

    return fastapi_app
