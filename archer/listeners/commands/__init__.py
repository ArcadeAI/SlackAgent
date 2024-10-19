from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slack_bolt import App

from archer.constants import BOT_NAME
from archer.listeners.commands.command import command_callback


def register_commands(app: "App"):
    app.command(f"/{BOT_NAME}")(command_callback)

