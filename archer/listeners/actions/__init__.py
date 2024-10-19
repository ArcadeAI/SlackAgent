from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slack_bolt import App

from archer.listeners.actions.user_settings import set_user_settings


def register_actions(app: "App"):
    app.action("Model")(set_user_settings)
