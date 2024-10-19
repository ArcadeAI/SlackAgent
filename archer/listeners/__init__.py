from archer.listeners.actions import register_actions
from archer.listeners.commands import register_commands
from archer.listeners.events import register_events


def register_listeners(app):
    register_actions(app)
    register_commands(app)
    register_events(app)

