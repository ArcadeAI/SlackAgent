from slack_bolt import App

from archer.listeners.events.assistant import assistant
from archer.listeners.events.home_opened import app_home_opened_callback


def register_events(app: App):
    # Register the App Home event
    app.event("app_home_opened")(app_home_opened_callback)
    # Register the assistant middleware for handling DM and thread messages
    app.assistant(assistant)
