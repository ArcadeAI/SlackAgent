from slack_bolt import App

from archer.listeners.actions.set_user_settings import set_user_settings


def register_actions(app: App):
    app.action("Model")(set_user_settings)
