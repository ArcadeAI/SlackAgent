# Slack AI Chatbot

This Slack chatbot app template offers a customizable solution for integrating AI-powered conversations into your Slack workspace. Here's what the app can do out of the box:

* Interact with the bot by mentioning it in conversations and threads
* Send direct messages to the bot for private interactions
* Use the `/ask-bolty` command to communicate with the bot in channels where it hasn't been added
* Utilize a custom function for integration with Workflow Builder to summarize messages in conversations
* Select your preferred API/model from the app home to customize the bot's responses
* Bring Your Own Language Model [BYO LLM](#byo-llm) for customization
* Custom FileStateStore creates a file in /data per user to store API/model preferences

Inspired by [ChatGPT-in-Slack](https://github.com/seratch/ChatGPT-in-Slack/tree/main)

Before getting started, make sure you have a development workspace where you have permissions to install apps. If you don’t have one setup, go ahead and [create one](https://slack.com/create).
## Installation

#### Prerequisites
* To use the OpenAI and Anthropic models, you must have an account with sufficient credits.
* To use the Vertex models, you must have [a Google Cloud Provider project](https://cloud.google.com/vertex-ai/generative-ai/docs/start/quickstarts/quickstart-multimodal#expandable-1) with sufficient credits.

#### Create a Slack App
1. Open [https://api.slack.com/apps/new](https://api.slack.com/apps/new) and choose "From an app manifest"
2. Choose the workspace you want to install the application to
3. Copy the contents of [manifest.json](./manifest.json) into the text box that says `*Paste your manifest code here*` (within the JSON tab) and click *Next*
4. Review the configuration and click *Create*
5. Click *Install to Workspace* and *Allow* on the screen that follows. You'll then be redirected to the App Configuration dashboard.

#### Environment Variables
Before you can run the app, you'll need to store some environment variables.

1. Open your apps configuration page from this list, click **OAuth & Permissions** in the left hand menu, then copy the Bot User OAuth Token. You will store this in your environment as `SLACK_BOT_TOKEN`.
2. Click ***Basic Information** from the left hand menu and follow the steps in the App-Level Tokens section to create an app-level token with the `connections:write` scope. Copy this token. You will store this in your environment as `SLACK_APP_TOKEN`.

```zsh
# Run these commands in the terminal. Replace with your app token, bot token, and the token for whichever API(s) you plan on using 
export SLACK_BOT_TOKEN=<your-bot-token>
export SLACK_APP_TOKEN=<your-app-token>
export OPENAI_API_KEY=<your-api-key>
export ANTHROPIC_API_KEY=<your-api-key>
```

##### Google Cloud Vertex AI Setup

To use Google Cloud Vertex AI, [follow this quick start](https://cloud.google.com/vertex-ai/generative-ai/docs/start/quickstarts/quickstart-multimodal#expandable-1) to create a project for sending requests to the Gemini API, then gather [Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc) with the strategy to match your development environment.

Once your project and credentials are configured, export environment variables to select from Gemini models:

```zsh
export VERTEX_AI_PROJECT_ID=<your-project-id>
export VERTEX_AI_LOCATION=<location-to-deploy-model>
```

The project location can be located under the **Region** on the [Vertex AI](https://console.cloud.google.com/vertex-ai) dashboard, as well as more details about available Gemini models.

### Setup Your Local Project
```zsh
# Clone this project onto your machine
git clone https://github.com/slack-samples/bolt-python-ai-chatbot.git

# Change into this project directory
cd bolt-python-ai-chatbot

# Setup your python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the dependencies
pip install -r requirements.txt

# Start your local server
python3 app.py
```

#### Linting
```zsh
# Run flake8 from root directory for linting
flake8 *.py && flake8 listeners/

# Run black from root directory for code formatting
black .
```

## Project Structure

### `manifest.json`

`manifest.json` is a configuration for Slack apps. With a manifest, you can create an app with a pre-defined configuration, or adjust the configuration of an existing app.


### `app.py`

`app.py` is the entry point for the application and is the file you'll run to start the server. This project aims to keep this file as thin as possible, primarily using it as a way to route inbound requests.


### `/listeners`

Every incoming request is routed to a "listener". Inside this directory, we group each listener based on the Slack Platform feature used, so `/listeners/commands` handles incoming [Slash Commands](https://api.slack.com/interactivity/slash-commands) requests, `/listeners/events` handles [Events](https://api.slack.com/apis/events-api) and so on.

### `/ai`

* `ai_constants.py`: Defines constants used throughout the AI module.

<a name="byo-llm"></a>
#### `ai/providers`
This module contains classes for communicating with different API providers, such as [Anthropic](https://www.anthropic.com/), [OpenAI](https://openai.com/), and [Vertex AI](cloud.google.com/vertex-ai). To add your own LLM, create a new class for it using the `base_api.py` as an example, then update `ai/providers/__init__.py` to include and utilize your new class for API communication.

* `__init__.py`: 
This file contains utility functions for handling responses from the provider APIs and retrieving available providers.

### `/state_store`

* `user_identity.py`: This file defines the UserIdentity class for creating user objects. Each object represents a user with the user_id, provider, and model attributes.

* `user_state_store.py`: This file defines the base class for FileStateStore.

* `file_state_store.py`: This file defines the FileStateStore class which handles the logic for creating and managing files for each user.

* `set_user_state.py`: This file creates a user object and uses a FileStateStore to save the user's selected provider to a JSON file.

* `get_user_state.py`: This file retrieves a users selected provider from the JSON file created with `set_user_state.py`.

## App Distribution / OAuth

Only implement OAuth if you plan to distribute your application across multiple workspaces. A separate `app_oauth.py` file can be found with relevant OAuth settings.

When using OAuth, Slack requires a public URL where it can send requests. In this template app, we've used [`ngrok`](https://ngrok.com/download). Checkout [this guide](https://ngrok.com/docs#getting-started-expose) for setting it up.

Start `ngrok` to access the app on an external network and create a redirect URL for OAuth. 

```
ngrok http 3000
```

This output should include a forwarding address for `http` and `https` (we'll use `https`). It should look something like the following:

```
Forwarding   https://3cb89939.ngrok.io -> http://localhost:3000
```

Navigate to **OAuth & Permissions** in your app configuration and click **Add a Redirect URL**. The redirect URL should be set to your `ngrok` forwarding address with the `slack/oauth_redirect` path appended. For example:

```
https://3cb89939.ngrok.io/slack/oauth_redirect
```
