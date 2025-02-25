<!-- A placeholder for a toolkit logo or cover image. Remove or replace with your own. -->
<h3 align="center">
  <a name="readme-top"></a>
  <img
    src="https://docs.arcade.dev/images/logo/arcade-logo.png"
    style="width: 250px;"
  >
</h3>

<br>

# Archer

Archer is a LLM Agent that lives in your slack workspace and can help you with your work.
Using Arcade, Archer can access and use various services like Google, Github, and more all
from within Slack.

By default, Archer can work with
- Google (Calendar, Mail, etc
- GitHub
- Slack

However, any of the available Arcade toolkits or custom toolkits you develop can also be
used by Archer.


## Install

### Prerequisites

- Python 3.10+
- Poetry 1.8.4+ <2.0.0
- Slack App
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

Instructions TODO

## Deploy on Modal

Set the environment variables for Slack, Arcade, and OpenAI

```bash
touch .env
```

```bash
SLACK_BOT_TOKEN=xxx
SLACK_SIGNING_SECRET=xxx
OPENAI_API_KEY=xxx
ARCADE_API_KEY=xxxx
LOG_LEVEL=INFO
```

### Deploy on Modal

You may need to first install the modal CLI and login

```bash
pip install modal
modal setup
```

Then deploy the app

```bash
make deploy
```
