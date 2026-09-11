# Agent Employees

A multi-agent bot that acts as your personal AI team. Give it a task and it plans the work, delegates to the right specialists, and shows live progress in **Discord** or **Slack**.

Built with [LangChain](https://github.com/langchain-ai/langchain), [discord.py](https://github.com/Rapptz/discord.py), and [slack-bolt](https://github.com/slackapi/bolt-python). Orchestration (planning + step dispatch) is hand-rolled in `bot.py`/`slack_bot.py`; a [LangGraph](https://github.com/langchain-ai/langgraph) state-graph version of the same flow lives in `graph/workflow.py` as an alternate implementation, not the default entry path.

---

## Table of Contents

- [How it works](#how-it-works)
- [Agents](#agents)
- [Tools](#tools)
- [Usage](#usage)
- [LLM Providers](#llm-providers)
- [Setup](#setup)
  - [1. Clone and install](#1-clone-and-install)
  - [2. Create a Discord bot](#2-create-a-discord-bot)
  - [2b. Create a Slack bot](#2b-create-a-slack-bot-optional--skip-if-using-discord-only)
  - [3. Configure environment](#3-configure-environment)
  - Optional: Semantic memory with Pinecone (collapsed, under Setup)
  - Optional: Google Workspace MCP (collapsed, under Setup)
  - [4. Run](#4-run)
- [Deployment](#deployment)
- [Adding a new agent](#adding-a-new-agent)
- [Adding a new tool](#adding-a-new-tool)
- [Project structure](#project-structure)
- [License](#license)

---

## How it works

Most messages go through a **Planner** that breaks the task into steps and assigns each one to a specialist agent. Agents pass context to one another so each step builds on the last. Progress is shown live as each step completes.

Plans are validated before any agent runs: 1–8 steps, supported agent names, nonempty tasks, and a specific role for each expert. Plans with three or more steps must end with a summarizer. An invalid plan gets one repair attempt; if it still fails validation, the bot reports the failure without executing any steps.

For simple requests, you can bypass planning by prefixing the message with `writer:`, `researcher:`, or `expert:`.

```
You: @agent-employees build a content strategy for my AI startup

🧠 Planning your task... · `gpt-4o-mini`
↓
Running plan:
✅ 1. RESEARCHER — current AI startup trends
⚙️ 2. EXPERT: Marketing Strategist
⏳ 3. SUMMARIZER
↓
[STEP 1 — RESEARCHER] ...
[STEP 2 — EXPERT: Marketing Strategist] ...
[FINAL SYNTHESIS] ...
gpt-4o-mini · 3,241 tokens · $0.00048
```

---

## Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Planner** | Breaks any task into steps, assigns agents, coordinates context passing | — |
| **Researcher** | Web search, fact-finding, trend analysis, current events | `web_search`, `read_file` |
| **Writer** | Emails, blog posts, social media copy, articles, drafts | — |
| **Expert** | Any domain expertise — Planner assigns a specific role (e.g. Senior Software Engineer, Senior AI Engineer, Product Manager) | `read_file`, `run_python`, memory tools, Google Workspace MCP tools |
| **Summarizer** | Synthesizes outputs from multiple agents into a final response | — |

---

## Tools

| Tool | Available to | Description |
|------|-------------|-------------|
| `web_search` | Researcher | DuckDuckGo web search |
| `read_file` | Researcher, Expert | Read any local file — text, code, PDF |
| `run_python` | Expert | Execute Python code for calculations or data analysis |
| `save_memory` | Expert | Persist a fact or preference across conversations |
| `recall_memory` | Expert | Retrieve a previously saved memory (semantic if Pinecone backend is enabled) |
| `list_memories` | Expert | List all stored memories |
| `delete_memory` | Expert | Remove a stored memory |
| `mcp_create_drive_folder` | Expert | Create Google Drive folders via MCP |
| `mcp_create_google_doc` | Expert | Create Google Docs via MCP |
| `mcp_create_google_slides` | Expert | Create Google Slides decks via MCP |
| `mcp_create_google_sheet` | Expert | Create Google Sheets spreadsheets via MCP |

---

## Usage

**Let the Planner decide (recommended for complex tasks):**
```
@agent-employees review this system architecture: ...
@agent-employees write a cold outreach email to a VC firm
@agent-employees what are the best index funds for a UK investor?
@agent-employees read /path/to/report.pdf and summarise it
```

**Target an agent directly (faster for simple tasks):**
```
@agent-employees writer: write a tweet about multi-agent AI
@agent-employees researcher: latest news on OpenAI
@agent-employees expert: remember that my preferred tone is direct and concise
```

**Follow-up questions work across messages:**
```
@agent-employees what is the best Python web framework?
@agent-employees what was my previous question?
@agent-employees expand on that
```

In Discord, you can `@mention` the bot in a server or send it a DM. In Slack, `@mention` it in a channel where it has been invited. The active model is shown after every response, and OpenAI runs also show token usage and estimated cost.

Runtime data is stored locally by default:
- Conversation history: `conversation_history.json`
- Local memory: `agent_memory.json`
- Pinecone delete manifest: `agent_memory_manifest.json`

---

## LLM Providers

Supports **OpenAI**, **Claude**, and **Ollama** (local models). Set `LLM_PROVIDER` in your `.env` to choose the default provider, or override it per run with `--provider`.

```env
# OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# Anthropic / Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here
CLAUDE_MODEL=claude-sonnet-4-6

# Ollama (local — run `ollama serve` first)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2     # or mistral, qwen2.5, etc.
OLLAMA_BASE_URL=http://localhost:11434
```

> **Note:** The Researcher uses tool calling (web search). This requires a model that supports it — `llama3.1`, `llama3.2`, `qwen2.5`, and `mistral-nemo` all work. Older models will answer from training data only.

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/eburakelevli/agent-employees.git
cd agent-employees
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Requires Python 3.10 or newer.

### 2. Create a Discord bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. **New Application** → name it → go to the **Bot** tab
3. Click **Reset Token** → copy it
4. Under **Privileged Gateway Intents**, enable **Message Content Intent**
5. Go to **OAuth2 → URL Generator** → select scope `bot` → permissions: `Send Messages`, `Read Message History`, `View Channels`
6. Open the generated URL in your browser to add the bot to your server

### 2b. Create a Slack bot (optional — skip if using Discord only)

> Uses **Socket Mode** — no public URL or server needed, works locally or on Railway out of the box.

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Name it (e.g. `agent-employees`) and pick your workspace → **Create App**

**Enable Socket Mode:**
3. In the left sidebar go to **Socket Mode** → toggle **Enable Socket Mode** ON
4. It will prompt you to create an App-Level Token — name it anything, grant the `connections:write` scope → **Generate**
5. Copy the token (starts with `xapp-`) — this is your `SLACK_APP_TOKEN`

**Add Bot permissions:**
6. Go to **OAuth & Permissions** in the sidebar
7. Under **Bot Token Scopes** add: `app_mentions:read`, `chat:write`, `channels:history`, `im:history`
8. Go to **Install App** → **Install to Workspace** → Allow
9. Copy the **Bot User OAuth Token** (starts with `xoxb-`) — this is your `SLACK_BOT_TOKEN`

**Subscribe to events:**
10. Go to **Event Subscriptions** → toggle **Enable Events** ON
11. Under **Subscribe to bot events** add: `app_mention`
12. Click **Save Changes**

**Invite the bot to a channel:**
13. In Slack, open any channel → type `/invite @agent-employees`

Add both tokens to your `.env`:
```env
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_APP_TOKEN=xapp-your-token-here
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your keys — see `.env.example` for all available options.

Set the token for the platform you plan to run, plus credentials for your chosen LLM provider:

```env
# Discord mode
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Slack mode
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_APP_TOKEN=xapp-your-token-here

# Pick one provider
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
```

<details>
<summary><strong>Optional: Semantic memory with Pinecone</strong> (click to expand)</summary>

By default, memory is a local JSON key-value store (`agent_memory.json`).

To enable semantic memory (vector search), set `MEMORY_BACKEND=pinecone` and provide Pinecone plus OpenAI credentials. The `pinecone` package is already included in `requirements.txt`.

> **Note:** Semantic memory uses OpenAI embeddings, so `OPENAI_API_KEY` is required even when your chat provider is Claude or Ollama.

Then add to your `.env`:

```env
MEMORY_BACKEND=pinecone
MEMORY_EMBEDDING_MODEL=text-embedding-3-small
MEMORY_TOP_K=3

PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=agent-employees-memory
PINECONE_NAMESPACE=default
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

To confirm it's active, check the startup log — you should see:
```
Memory backend: Pinecone (index=agent-employees-memory, namespace=default)
```
If it says `local`, one of the required env vars is missing or the package isn't installed.

**Viewing your vectors:** Go to [console.pinecone.io](https://console.pinecone.io) → select your index → **Namespace** tab to browse records and inspect metadata (`key`, `value`, `created_at`). The **Metrics** tab shows read/write usage and storage.

How it works:
- `save_memory(key, value)` embeds the memory text and upserts it to Pinecone with metadata.
- `recall_memory(query)` performs semantic similarity search and returns the best match.
- `list_memories()` reads known memory keys from a local manifest used for stable deletes.
- `delete_memory(key)` removes the corresponding vector by ID from Pinecone.

If Pinecone credentials or dependencies are missing, the app continues using local memory.

</details>

<details>
<summary><strong>Optional: Google Workspace MCP (Drive/Docs/Slides/Sheets)</strong> (click to expand)</summary>

This repo calls a remote/local MCP server over HTTP. It does not host Google OAuth directly and does not need your Google OAuth client secret.

How the pieces fit:
- `agent-employees` is the MCP client. It sends JSON-RPC calls to `GOOGLE_WORKSPACE_MCP_URL`.
- The Google Workspace MCP server is a separate process you run locally/remotely.
- Google OAuth credentials (`client_id` / `client_secret`) are for the MCP server process, not this repo's app process.
- `GOOGLE_WORKSPACE_USER_EMAIL` tells the MCP server which already-authorized Google account to use. It does not grant access by itself; access comes from the Google OAuth consent flow.

#### 1) Create Google OAuth credentials

In Google Cloud Console:

1. Create or select a Google Cloud project.
2. Enable these APIs:
   - Google Drive API
   - Google Sheets API
3. Go to **APIs & Services -> OAuth consent screen**.
4. For personal Gmail accounts, use:
   - User type: `External`
   - Publishing status: `Testing`
   - Test users: add your Gmail address
5. Go to **APIs & Services -> Credentials**.
6. Create an **OAuth client ID**.
7. Use application type **Desktop app**.
8. Copy the generated:
   - Client ID
   - Client secret

Do not publish the app for local testing. Keeping it in `Testing` limits authorization to the test users you add.

#### 2) Start a Google Workspace MCP server separately

One working MCP server option:
- [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp)

In a separate terminal, export the Google OAuth values for the MCP server process, then start it:

```bash
export GOOGLE_OAUTH_CLIENT_ID="your_client_id.apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="your_client_secret"
uvx workspace-mcp --transport streamable-http
```

First run may prompt an OAuth login flow in your browser.

Keep this MCP terminal running while the bot is running.

#### 3) Configure this app

Set these in `.env`:

```env
GOOGLE_WORKSPACE_MCP_URL=http://127.0.0.1:8000/mcp
GOOGLE_WORKSPACE_MCP_BEARER_TOKEN=
GOOGLE_WORKSPACE_MCP_TIMEOUT_SECONDS=30
GOOGLE_WORKSPACE_USER_EMAIL=your.email@gmail.com
```

`GOOGLE_WORKSPACE_MCP_BEARER_TOKEN` is only needed if your MCP server requires bearer auth.
`GOOGLE_WORKSPACE_MCP_URL` is the MCP endpoint this app will call (default local path: `/mcp` on port `8000`).
`GOOGLE_WORKSPACE_USER_EMAIL` must match the Google account you authorized in the MCP browser OAuth flow.

Do not put `GOOGLE_OAUTH_CLIENT_SECRET` in this repo's `.env` unless you also change your MCP server startup to read it from there. This app does not use that value.

#### 4) Verify MCP endpoint

Quick browser click to `/mcp` may show:
- `406 Not Acceptable` (expected for plain browser requests)

The endpoint is still healthy as long as the server process is running.

#### 5) Run and test

Restart the app after env changes:

Discord:

```bash
python main.py --provider openai
```

Slack:

```bash
python main.py --slack --provider openai
```

Then test direct Expert tool usage:

```text
@agent-employees expert: use mcp_create_google_sheet with title "AE MCP Sheet" and folder_id "root"
```

Create a Drive folder:

```text
@agent-employees expert: use mcp_create_drive_folder to create a folder named "AE MCP Test". Return only the folder ID.
```

Create a spreadsheet in that folder:

```text
@agent-employees expert: use mcp_create_google_sheet with title "AE MCP Sheet", folder_id "<PASTE_FOLDER_ID>"
```

#### Notes

- If you do not pass `folder_id` / `parent_folder_id`, tools default to Google Drive `root`.
- To find a folder ID, open the folder in Google Drive and copy the part after `/folders/` in the URL.
- If Slack still says MCP URL is not configured, restart the bot process after editing `.env`.
- For reliable tool calling during setup, prefer `LLM_PROVIDER=openai` or `LLM_PROVIDER=claude`.
- If startup logs show `Google Workspace MCP: not configured`, `.env` was not loaded or the key is missing.
- Removing `GOOGLE_WORKSPACE_USER_EMAIL` disables this app from selecting your Google account, but it does not revoke OAuth access. Revoke access from Google Account -> Security -> Third-party apps & services.

</details>

### 4. Run

**Discord:**
```bash
python main.py
```

**Slack:**
```bash
python main.py --slack
```

**Override the LLM provider for one run:**
```bash
python main.py --provider openai
python main.py --provider claude
python main.py --provider ollama
python main.py --slack --provider ollama
```

---

## Deployment

For 24/7 uptime without running it locally, deploy to [Railway](https://railway.app):

1. Push this repo to GitHub
2. New Project → Deploy from GitHub repo
3. Add your environment variables in the **Variables** tab
4. Railway auto-deploys on every push

The included `Procfile` runs Discord mode:

```procfile
worker: python main.py
```

To run Slack mode on Railway, set the service start command to `python main.py --slack` or update the `Procfile`.

---

## Adding a new agent

1. Create `agents/your_agent.py` with an `async def run_your_agent(task: str) -> str` function
2. Add it to `_dispatch` in both `bot.py` (Discord) and `slack_bot.py` (Slack)
3. Add it to the available agents list in the Planner prompt in `agents/planner.py`
4. If you want direct-prefix support, add it to the forced-agent list in both `bot.py` and `slack_bot.py`

## Adding a new tool

1. Create `tools/your_tool.py` with a `@tool` decorated function
2. Import it in the relevant agent(s) and add it to that agent's `bind_tools(...)` call

---

## Project structure

```
agent-employees/
├── agents/
│   ├── expert.py       # Generic expert — any role assigned by the Planner
│   ├── planner.py      # Creates execution plans from user tasks
│   ├── researcher.py   # Web search + file reading
│   ├── summarizer.py   # Synthesizes multi-agent outputs
│   └── writer.py       # Content and copy writing
├── tools/
│   ├── code_runner.py  # Python code execution
│   ├── file_reader.py  # Local file reading (text + PDF)
│   ├── history.py      # Per-user conversation history
│   ├── mcp_google_workspace.py # Google Workspace MCP tools
│   └── memory.py       # Local or Pinecone-backed semantic memory
├── graph/
│   └── workflow.py     # LangGraph state-graph alternate implementation (bot.py/slack_bot.py is the default entry path)
├── bot.py              # Discord bot — orchestration, progress updates
├── slack_bot.py        # Slack bot — same logic, Socket Mode transport
├── config.py           # Environment variable loading
├── llm.py              # LLM provider factory (OpenAI / Ollama / Claude)
├── main.py             # Entry point (--slack flag for Slack mode)
└── requirements.txt
```

---

## License

MIT — see [LICENSE](LICENSE).
