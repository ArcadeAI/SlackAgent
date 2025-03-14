from logging import Logger

from slack_sdk import WebClient

from archer.defaults import get_available_models
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
            (option for option in options if option["value"].startswith(initial_model)), None
        )
        if initial_option is None:
            initial_option = options[-1]
    except Exception:
        logger.exception("Error finding initial option")
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
                            "text": "Archer Settings",
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
                                        "text": "Select your preferred model",
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
    except Exception:
        logger.exception("Error publishing home view")
