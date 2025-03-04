from slack_bolt import App

from archer.listeners.actions.auth_complete import handle_auth_complete
from archer.listeners.actions.auth_complete_button import handle_auth_complete_button
from archer.listeners.actions.user_settings import set_user_settings


def register_actions(app: App):
    app.action("Model")(set_user_settings)
    app.view("auth_complete")(handle_auth_complete)
    app.action("auth_complete_button")(handle_auth_complete_button)
