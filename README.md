<h3 align="center">
  <a name="readme-top"></a>
  <img
    src="https://docs.arcade.dev/images/logo/arcade-logo.png"
    style="width: 250px;"
  >
</h3>

<br>

# Archer: Agentic Slack Assistant

Archer is a AI Agent that lives in your slack workspace and can help you with your work.
Using Arcade, Archer can access and use various services like Google, Github, and more all
from within Slack.

<div style="text-align: center;">
<video width="640" height="360" style="border-radius: 10px;" controls>
  <source src="https://raw.githubusercontent.com/ArcadeAI/SlackAgent/77334945accf5f2f7758c7fafd17520a198f6ba5/assets/Archer%20Demo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>
</div>





## Features

By default, Archer can interact with and use:
- Google Mail
- Google Calendar
- GitHub
- Search Engine (Serp)
- Crawling and web scraping (firecrawl)

However, any of the available Arcade toolkits or custom toolkits you develop can also be
used by Archer.

You can change the prompt and tools used by Archer by editing
the ``defaults.py`` file.

For the names of all Arcade cloud tools you can use ``arcade show`` in your terminal,
or visit [https://docs.arcade.dev/integrations](https://docs.arcade.dev/integrations).

## Agent

The agent is built using the [LangGraph](https://langchain.com/langgraph) framework.

The graph for the agent is shown below:

<div style="text-align: center; width: 80%; height: 80%; margin: 0 auto; border-radius: 15px; overflow: hidden;">
  <img src="https://raw.githubusercontent.com/ArcadeAI/SlackAgent/77334945accf5f2f7758c7fafd17520a198f6ba5/assets/Archer-Graph.png" alt="Archer Graph" />
</div>

<br>

## Screenshots

Archer uses the Slack Assistant UI so it's available on across the entire slack app.

<div style="text-align: center;">
  <img style="display: inline-block; width: 45%; margin: 0 10px;" alt="Screenshot 2025-03-04 at 3 23 46 AM" src="https://github.com/user-attachments/assets/22db9c33-36bf-414f-b04f-c70234552144" />
  <img style="display: inline-block; width: 45%; margin: 0 10px;" alt="Screenshot 2025-03-04 at 3 25 23 AM" src="https://github.com/user-attachments/assets/f743d286-6bde-4995-b5a0-77e8d32f203d" />
</div>



<br>
<br>
<br>

## Self-Hosted Archer for your Slack

Archer is not distributed as a Slack app, but you can easily self-host it the
same way shown above.


### Prerequisites

- Python 3.10+
- Poetry 1.8.4+ <2.0.0
- OpenAI API Key
- Arcade API Key (see [Arcade](https://docs.arcade.dev/home/api-keys))


### Install Archer

Clone the repository

```bash
git clone https://github.com/arcadeai/archer.git

```
Then install the local dependencies

```bash
cd archer
make install
```

### Get a Slack App

1. Open [https://api.slack.com/apps/new](https://api.slack.com/apps/new) and choose "From an app manifest"
2. Choose the workspace where you want to install Archer
3. Copy the contents of [config/manifest.json](./config/manifest.json) into the text box that says "*Paste your manifest code here*" (within the JSON tab) and click *Next*
4. Review the configuration and click *Create*
5. In the app configuration page, go to "App Home" in the left sidebar and ensure the Home Tab and Messages Tab are enabled
6. Under "App Manifest" in the left sidebar, find the `event_subscriptions.request_url` and `interactivity.request_url` fields
7. After you deploy Archer to Modal, replace `<INSERT>` in both URLs with your Modal app URL
8. Click *Install to Workspace* and *Allow* on the screen that follows

You'll need two values from the Slack App for your .env file:
- From **OAuth & Permissions**, copy the **Bot User OAuth Token** (for `SLACK_BOT_TOKEN`)
- From **Basic Information**, copy the **Signing Secret** (for `SLACK_SIGNING_SECRET`)


### Setup Modal

If you haven't already, install the Modal CLI and set it up:
```bash
pip install modal
modal setup
```


### Setup Environment

Set the environment variables for Slack, Arcade, and OpenAI

```bash
touch .env
```

```bash

SLACK_BOT_TOKEN=<slack-bot-token>
SLACK_SIGNING_SECRET=<slack-signing-secret>
OPENAI_API_KEY=<openai-api-key>
ARCADE_API_KEY=<arcade-api-key>
LOG_LEVEL=INFO

LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY=<langsmith-api-key>
LANGSMITH_PROJECT="archer"

SLACK_BOT_TOKEN=xxx
SLACK_SIGNING_SECRET=xxx
OPENAI_API_KEY=xxx
ARCADE_API_KEY=xxxx
LOG_LEVEL=INFO

```

### Deploy on Modal

Then deploy the app

```bash
make deploy
```

Modal will deploy the app and provide you with a URL to access it.


### Set Request URLs

In the Slack App configuration page, go to "Event Subscriptions" in the left sidebar and find the `request_url` field.
Replace `<INSERT>` with your Modal app URL.

In the Slack App configuration page, go to "Interactivity & Shortcuts" in the left sidebar and find the `request_url` field.
Replace `<INSERT>` with your Modal app URL.

or just replace in the manifest.json file in the JSON tab in the Slack App configuration page.
