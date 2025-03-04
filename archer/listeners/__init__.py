from archer.listeners.actions import register_actions
from archer.listeners.events import register_events


def register_listeners(app):
    register_actions(app)
    register_events(app)
