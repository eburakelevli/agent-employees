# Agent Employees

An AI assistant for **Discord and Slack** that splits a request into focused tasks, assigns them to specialist agents, and brings their work together.

Use it to research a topic, draft content, review an idea, or work with local files. Choose **OpenAI**, **Claude**, or a local model through **Ollama**. Optional integrations add semantic memory with Pinecone and file creation in Google Workspace.

Give it a task in plain language:

```text
@agent-employees research developer onboarding practices and draft a checklist for our team
```

The bot plans the work, shows which agent is running, and posts the results when the plan finishes. For a quick request, you can choose an agent directly:

```text
@agent-employees writer: make this introduction shorter and more welcoming: ...
```

## Contents

- [How it works](#how-it-works)
- [Getting started](#getting-started)
- [Using the bot](#using-the-bot)
- [Optional integrations](#optional-integrations)
- [Data and current limitations](#data-and-current-limitations)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

## How it works

For a normal request, the **Planner** creates a sequence of steps. Each agent receives the original request and the outputs of earlier steps, so it can build on their work.

| Agent | What it does | Available tools |
| --- | --- | --- |
| **Planner** | Breaks the request into steps and chooses the agents | — |
| **Researcher** | Searches the web and gathers information | Web search, local file reading |
| **Writer** | Drafts and edits emails, articles, posts, and other copy | — |
| **Expert** | Handles analysis or tool use in an assigned role, such as Software Engineer or Marketing Strategist | Local file reading, Python execution, memory, Google Workspace |
| **Summarizer** | Combines earlier outputs into a final response | — |

Plans are validated **before any step runs**. They must contain 1–8 steps, supported agent names, nonempty tasks, and a specific role for each expert. Plans with three or more steps must end with a summarizer. If validation fails, the planner gets one repair attempt. A second failure stops execution and produces a clear error.

The `writer:`, `researcher:`, and `expert:` prefixes skip planning and run that agent directly.

## Getting started

You'll need **Python 3.10 or newer**, a Discord or Slack bot, and credentials for your chosen model provider. For Ollama, you'll need a running local server and a downloaded model.

Pinecone and Google Workspace are optional. You can get the bot running first and add them later.

### 1. Install the project

```bash
git clone https://github.com/eburakelevli/agent-employees.git
cd agent-employees
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, use `.venv\Scripts\Activate.ps1` to activate the environment and `Copy-Item .env.example .env` to copy the configuration file.

### 2. Connect a chat platform

Choose the platform you want to use. Each bot process connects to one platform.

<details>
<summary><strong>Discord setup</strong></summary>

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and create an application.
2. Open **Bot**, generate or reset the bot token, and copy it.
3. Under **Privileged Gateway Intents**, enable [Message Content Intent](https://docs.discord.com/developers/events/gateway#message-content-intent).
4. In **OAuth2 → URL Generator**, select the `bot` scope and the permissions **View Channels**, **Send Messages**, and **Read Message History**.
5. Open the generated invite URL and add the bot to your server.
6. Set the token in your `.env` file:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token
```

You can mention the bot in a server channel or send it a direct message.

</details>

<details>
<summary><strong>Slack setup</strong></summary>

The Slack bot uses [Socket Mode](https://docs.slack.dev/apis/events-api/using-socket-mode/), so it doesn't need a public HTTP endpoint.

1. Open [Your Apps](https://api.slack.com/apps), choose **Create New App → From scratch**, and select your workspace.
2. Enable **Socket Mode**. Create an app-level token with the `connections:write` scope. This token starts with `xapp-`.
3. Under **OAuth & Permissions → Bot Token Scopes**, add [`app_mentions:read`](https://docs.slack.dev/reference/events/app_mention/) and [`chat:write`](https://docs.slack.dev/reference/scopes/chat.write/).
4. Under **Event Subscriptions**, enable events and subscribe to the bot event `app_mention`. Save your changes.
5. Install the app to your workspace and copy its **Bot User OAuth Token**, which starts with `xoxb-`. Reinstall the app if you change its scopes later.
6. Invite the bot to a channel with `/invite @agent-employees`, using your app's actual name.
7. Set both tokens in `.env`:

```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
```

Mention the bot in a channel it has joined. This implementation listens for channel mentions; it does not handle Slack direct messages.

</details>

### 3. Choose a model provider

Edit `.env` using **one** of the configurations below. You only need credentials for the provider you choose, unless you also enable Pinecone memory.

<details open>
<summary><strong>OpenAI — the default provider</strong></summary>

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

</details>

<details>
<summary><strong>Anthropic / Claude</strong></summary>

```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your_anthropic_api_key
CLAUDE_MODEL=claude-sonnet-4-6
```

</details>

<details>
<summary><strong>Ollama — local models</strong></summary>

Start your Ollama server and download the model you want to use. Then configure:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

The Researcher and Expert require a model that supports tool calling. An incompatible model may fail when those agents run. Planning also requires reliable JSON output.

</details>

These examples use the defaults in [config.py](config.py). All available settings are listed in [.env.example](.env.example). Restart the bot after changing `.env`.

### 4. Run the bot

Run commands from the project directory with your virtual environment active.

| Platform | Command |
| --- | --- |
| Discord | `python main.py` |
| Slack | `python main.py --slack` |

To override the provider for one run:

```bash
python main.py --provider claude
python main.py --slack --provider ollama
```

Check the startup log for the selected provider, model, and integration settings. Then send a first message:

```text
@agent-employees writer: write a friendly welcome message for a new teammate
```

In a Discord DM, you can leave out the mention. Keep the process running while you use the bot.

## Using the bot

**Let the planner choose the steps:**

```text
@agent-employees research our competitors and draft a positioning statement: ...
@agent-employees review this architecture and suggest improvements: ...
@agent-employees read /path/to/report.pdf and summarise the main findings
```

File paths refer to files on the machine running the bot. Chat attachments are not downloaded automatically.

**Choose an agent directly:**

```text
@agent-employees writer: draft a short product launch announcement
@agent-employees researcher: find recent developments in open-source AI
@agent-employees expert: remember that my preferred writing tone is direct and concise
```

**Ask a follow-up:**

```text
@agent-employees make that draft more conversational
@agent-employees what was my previous question?
```

The bot includes recent conversation history with your next request. Successful requests show the active model; OpenAI requests also show token usage and an estimated cost.

## Optional integrations

### Semantic memory with Pinecone

<details>
<summary><strong>Setup and behavior</strong></summary>

By default, the Expert stores memories in a local JSON file and recalls them by exact key. Pinecone enables similarity search, so a related phrase can retrieve a saved memory.

Add these settings to `.env`:

```env
MEMORY_BACKEND=pinecone
OPENAI_API_KEY=your_openai_api_key
MEMORY_EMBEDDING_MODEL=text-embedding-3-small
MEMORY_TOP_K=3
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=agent-employees-memory
PINECONE_NAMESPACE=default
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

Memory embeddings use OpenAI even when your chat provider is Claude or Ollama. The app creates the named Pinecone index on first use if it doesn't exist.

The Expert has four memory tools:

| Tool | Behavior with Pinecone |
| --- | --- |
| `save_memory` | Embeds and saves a key/value pair |
| `recall_memory` | Searches for similar memories and returns the top match |
| `list_memories` | Lists keys recorded in the local manifest |
| `delete_memory` | Uses the local manifest to find and delete the vector |

After restarting, the startup log should show `Memory backend: Pinecone`. This confirms the configuration was selected; the connection is exercised when a memory tool runs. You can inspect stored vectors in the [Pinecone console](https://console.pinecone.io).

If required credentials or dependencies are missing, the app selects local memory. Once Pinecone is selected, a failed save or query returns an error rather than silently switching back to local storage.

Keep `agent_memory_manifest.json` alongside your deployment: the current implementation needs it to list and delete Pinecone memories.

</details>

### Google Workspace through MCP

<details>
<summary><strong>Setup and a first test</strong></summary>

The Expert can create Drive folders, Google Docs, Slides files, and spreadsheets through a separate **Model Context Protocol (MCP)** server. This repository contains the client; the server handles Google authentication and API access.

**1. Set up the MCP server.**

The integration uses tools exposed by [Google Workspace MCP](https://github.com/taylorwilsdon/google_workspace_mcp). Follow its [setup guide](https://workspacemcp.com/quick-start) to configure Google OAuth, enable the Google APIs you need, and authorise your account. Use its Streamable HTTP transport and enable the creation tools this client calls: `create_drive_folder`, `create_drive_file`, and `create_spreadsheet`.

Google OAuth client credentials belong to the MCP server's configuration. This bot does not read `GOOGLE_OAUTH_CLIENT_ID` or `GOOGLE_OAUTH_CLIENT_SECRET` or perform the MCP server's OAuth login flow.

**2. Connect the bot.**

Set the endpoint and authorised Google account in `.env`. For a server running locally on port 8000:

```env
GOOGLE_WORKSPACE_MCP_URL=http://127.0.0.1:8000/mcp
GOOGLE_WORKSPACE_USER_EMAIL=your.email@gmail.com
GOOGLE_WORKSPACE_MCP_BEARER_TOKEN=
GOOGLE_WORKSPACE_MCP_TIMEOUT_SECONDS=30
```

If the server requires a bearer token, supply it in `GOOGLE_WORKSPACE_MCP_BEARER_TOKEN`. The email selects an already-authorised account; it does not grant access on its own. For a remote server, use its actual endpoint.

**3. Restart the bot and create a test file.**

Keep the MCP server running, restart the bot, and send:

```text
@agent-employees expert: use mcp_create_google_sheet with title "Agent Employees Test" and folder_id "root"
```

To create a folder:

```text
@agent-employees expert: use mcp_create_drive_folder to create a folder named "Project Notes". Return the folder ID.
```

You can use that ID as `folder_id` in a later file-creation request. Without a folder ID, files are created in Drive's root folder.

The current Slides and Sheets tools create files; they do not populate slides, cells, or charts. The Docs tool also accepts initial text content. Tool availability and authentication must match your MCP server's configuration.

</details>

## Data and current limitations

The bot stores these files in its working directory. They are excluded from Git.

| File | Purpose |
| --- | --- |
| `conversation_history.json` | Last 10 exchanges per user; previous answers are shortened when included in a prompt |
| `agent_memory.json` | Local memory keys and values |
| `agent_memory_manifest.json` | Pinecone memory keys and vector IDs used for listing and deletion |

A few details matter when choosing where to run it:

- **Tool access:** Python execution runs with the bot process's permissions and environment. File reading can access files readable by that process. The app currently has no user allowlist or code-execution sandbox.
- **Shared context:** memory is shared across users of the bot instance. Conversation history is keyed by user, without channel or thread separation, so a later channel request can reuse context from a private conversation.
- **Response length:** chat output is currently truncated to fit the bot's message limits. Long documents may need a different delivery approach.

The current setup is best suited to personal use in an environment you control. These boundaries need additional work before opening the bot to untrusted users.

## Deployment

Run the bot as a persistent worker process. The included [Procfile](Procfile) starts Discord mode:

```procfile
worker: python main.py
```

For Slack, use `python main.py --slack` as the service's start command. Set your platform tokens and provider credentials through your host's environment settings.

If you use Railway, configure [persistent storage](https://docs.railway.com/volumes/reference) for runtime data you want to keep across deployments. The current storage paths are relative to the process's working directory, so your deployment must place those files on persistent storage. Run a single instance against the JSON files; they do not support concurrent writers safely.

A hosted bot also needs network access to its model provider and any MCP server. `127.0.0.1` refers to the bot's own host, so a hosted bot cannot use that address to reach a server on your laptop.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| The bot reports missing tokens | Replace the placeholders in `.env` for the platform you are running, then restart. |
| Discord does not respond | Enable Message Content Intent, check channel permissions, and mention the bot or use a DM. |
| Slack does not respond | Check Socket Mode, both tokens, the `app_mention` subscription, and the bot's channel membership. |
| The wrong model is running | Check `LLM_PROVIDER`, the matching model setting, and any `--provider` override. |
| An Ollama agent fails on tools | Check that the server is running, the model is downloaded, and it supports tool calling. |
| Planning fails after two attempts | Make the request more specific. No plan steps ran. If it keeps happening, check the model's JSON output capability. |
| Pinecone logs show local memory | Check `MEMORY_BACKEND`, Pinecone settings, the OpenAI key, and installed dependencies. |
| Google Workspace is not configured | Set `GOOGLE_WORKSPACE_MCP_URL` and restart the bot. |
| An MCP request fails | Check server logs, connectivity, bearer-token requirements, and Google account authorisation. |

For other failures, check the terminal running the bot for its error message.

## Development

The project uses LangChain for model and tool integration, `discord.py` for Discord, and `slack-bolt` for Slack. The default entry point runs the orchestration in `bot.py` or `slack_bot.py`. `graph/workflow.py` contains an alternate LangGraph implementation.

### Run the tests

From the project directory, after installing dependencies:

```bash
python -m unittest discover -s tests -v
```

The tests cover plan validation, the single repair attempt, and rejection of invalid plans before execution in Discord, Slack, and the graph workflow. They use mocked model calls and require no live service credentials.

### Add an agent

1. Create an async agent function in `agents/` that returns a response string.
2. Add the agent name to the `Step.agent` allowed values and describe it in `PLANNER_PROMPT` in `agents/planner.py`.
3. Register it in `_dispatch` in both `bot.py` and `slack_bot.py`.
4. For direct-prefix support, update each bot's prefix detection and `_run_single` dispatch.
5. If you use the alternate graph, update its routing and execution too. Add tests for the new behavior.

### Add a tool

Define the tool with LangChain's `@tool` decorator, then add it to `EXPERT_TOOLS` or `RESEARCHER_TOOLS` in the corresponding agent module. Those lists are used for both model tool binding and execution lookup. Update the agent prompt, and the planner prompt if the capability affects routing.

### Project layout

```text
agent-employees/
├── agents/                     # Planner, researcher, writer, expert, summarizer
├── tools/                      # Files, Python execution, history, memory, MCP
├── graph/workflow.py           # Alternate LangGraph workflow
├── tests/test_planner.py        # Plan validation and execution-boundary tests
├── bot.py                      # Discord handlers and orchestration
├── slack_bot.py                # Slack handlers and orchestration
├── config.py                   # Environment settings
├── llm.py                      # Model provider factory
├── main.py                     # CLI entry point
├── .env.example                # Configuration reference
├── requirements.txt            # Python dependencies
└── Procfile                    # Default worker command
```

## License

[MIT](LICENSE). You're welcome to use, adapt, and build on the project.
