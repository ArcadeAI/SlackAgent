from logging import Logger

from slack_sdk import WebClient

from archer.agent import get_available_models
from archer.env import BOT_NAME  # TODO: move to defaults
from archer.storage.functions import get_user_state


def app_home_opened_callback(event: dict, logger: Logger, client: WebClient):
    if event["tab"] != "home":
        return

    # Create a list of options for the dropdown menu
    options = [
        {
            "text": {
                "type": "plain_text",
                "text": f"{model_info['name']} ({model_info['provider']})",
                "emoji": True,
            },
            "value": f"{model_name} {model_info['provider'].lower()}",
        }
        for model_name, model_info in get_available_models().items()
    ]

    # Retrieve user's state to determine if they already have a selected model
    initial_model = get_user_state(event["user"])["model"]
    try:
        # Find the first option that matches the initial_model
        initial_option = next(
            (option for option in options if option["value"].startswith(initial_model)),
            None
        )
        if initial_option is None:
            initial_option = options[-1]
    except Exception as e:
        logger.error(e)
        initial_option = options[-1]

    try:
        client.views_publish(
            user_id=event["user"],
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"Welcome to {BOT_NAME}'s Home Page!",
                            "emoji": True,
                        },
                    },
                    {"type": "divider"},
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type": "text",
                                        "text": "Pick an option",
                                        "style": {"bold": True},
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "static_select",
                                "options": options,
                                "initial_option": initial_option,
                                "action_id": "Model",
                            }
                        ],
                    },
                ],
            },
        )
    except Exception as e:
        logger.error(e)
