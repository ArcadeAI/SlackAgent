from logging import Logger
from typing import Any

from slack_bolt import Ack

from archer.storage.functions import set_user_state


def set_user_settings(logger: Logger, ack: Ack, body: dict[str, Any]):
    try:
        ack()
        user_id = body["user"]["id"]
        value = body["actions"][0]["selected_option"]["value"]
        if value != "null" and value != "" and value is not None:
            # parsing the selected option value from the options array in app_home_opened.py
            selected_provider, selected_model = value.split(" ")[-1], value.split(" ")[0]
            set_user_state(user_id, selected_provider, selected_model)
        else:
            logger.warning(f"Invalid value selected: {value}")
            # TODO: raise to user
    except Exception:
        logger.exception("Error setting user settings")
