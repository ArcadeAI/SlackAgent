from slack_bolt import App

from archer.listeners.events.direct_message import direct_message_callback
from archer.listeners.events.home_opened import app_home_opened_callback
from archer.listeners.events.mentioned import app_mentioned_callback


def register(app: App):
    app.event("bot_home_opened")(app_home_opened_callback)
    app.event("bot_mention")(app_mentioned_callback)
    app.event("bot_direct_message")(direct_message_callback)
