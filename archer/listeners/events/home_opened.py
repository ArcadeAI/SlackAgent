from logging import Logger

from slack_sdk import WebClient

from archer.agent import get_available_models
from archer.constants import BOT_NAME
from archer.storage.functions import get_user_state


def app_home_opened_callback(event: dict, logger: Logger, client: WebClient):
    if event["tab"] != "home":
        return

    # create a list of options for the dropdown menu each containing the model name and provider
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

    # retrieve user's state to determine if they already have a selected model
    user_state = get_user_state(event["user"])
    initial_option = None

    if user_state:
        initial_option = list(filter(lambda x: x["value"].startswith(user_state["model"]), options))
    else:
        # add an empty option if the user has no previously selected model.
        options.append({
            "text": {"type": "plain_text", "text": "Select a model", "emoji": True},
            "value": "null",
        })

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
