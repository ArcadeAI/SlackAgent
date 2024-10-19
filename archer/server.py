import logging
from logging import Logger
from typing import Callable

from slack_bolt import Ack, App, BoltResponse, Respond, WebClient

from archer.constants import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
from archer.listeners import register_listeners

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

slack_app = App(
  logger=logger,
  signing_secret=SLACK_SIGNING_SECRET,
  token=SLACK_BOT_TOKEN
)


@slack_app.middleware
def log_request(logger: Logger, body: dict, next: Callable[[], BoltResponse]) -> BoltResponse:
    logger.debug(body)
    return next()

# register all the events, actions, commands, and function listeners
register_listeners(slack_app)


@slack_app.command("/archer")
def archer_handler(body: dict, ack: Ack, respond: Respond, client: WebClient, logger: Logger) -> None:
    ack()
    respond("Hello, Archer!")



