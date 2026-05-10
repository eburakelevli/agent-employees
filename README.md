# Agent Employees

A multi-agent Discord bot that acts as your personal AI team. Give it a task and it plans the work, delegates to the right specialists, and shows you live progress — all inside Discord.

Built with [LangGraph](https://github.com/langchain-ai/langgraph), [LangChain](https://github.com/langchain-ai/langchain), and [discord.py](https://github.com/Rapptz/discord.py).

---

## How it works

Every message goes through a **Planner** that breaks the task into steps and assigns each one to a specialist agent. Agents pass context to one another so each step builds on the last. Progress is shown live as each step completes.

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
| **Expert** | Any domain expertise — Planner assigns a specific role (e.g. Senior Software Engineer, Senior AI Engineer, Product Manager) | `read_file`, `run_python`, `save_memory`, `recall_memory`, `list_memories`, `delete_memory` |
| **Summarizer** | Synthesizes outputs from multiple agents into a final response | — |

---

## Tools

| Tool | Available to | Description |
|------|-------------|-------------|
| `web_search` | Researcher | DuckDuckGo web search |
| `read_file` | Researcher, Expert | Read any local file — text, code, PDF |
| `run_python` | Expert | Execute Python code for calculations or data analysis |
| `save_memory` | Expert | Persist a fact or preference across conversations |
| `recall_memory` | Expert | Retrieve a previously saved memory |
| `list_memories` | Expert | List all stored memories |
| `delete_memory` | Expert | Remove a stored memory |
| `mcp_create_drive_folder` | Expert | Create Google Drive folders via MCP |
| `mcp_create_google_doc` | Expert | Create Google Docs via MCP |
| `mcp_create_google_slides` | Expert | Create Google Slides decks via MCP |

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
```

**Follow-up questions work across messages:**
```
@agent-employees what is the best Python web framework?
@agent-employees what was my previous question?
@agent-employees expand on that
```

The active model and token usage are shown after every response.

---

## LLM Providers

Supports **OpenAI** and **Ollama** (local models). Set `LLM_PROVIDER` in your `.env` to switch.

```env
# OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# Ollama (local — run `ollama serve` first)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2        # or mistral, qwen2.5, etc.
OLLAMA_BASE_URL=http://localhost:11434
```

> **Note:** The Researcher uses tool calling (web search). This requires a model that supports it — `llama3.1`, `llama3.2`, `qwen2.5`, and `mistral-nemo` all work. Older models will answer from training data only.

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-username/agent-employees.git
cd agent-employees
pip install -r requirements.txt
```

### 2. Create a Discord bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. **New Application** → name it → go to the **Bot** tab
3. Click **Reset Token** → copy it
4. Under **Privileged Gateway Intents**, enable **Message Content Intent**
5. Go to **OAuth2 → URL Generator** → select scope `bot` → permissions: `Send Messages`, `Read Message History`, `View Channels`
6. Open the generated URL in your browser to add the bot to your server

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your keys — see `.env.example` for all available options.

### Optional: Google Workspace MCP (Drive/Docs/Slides)

If you run a compatible Google Workspace MCP server, set:

```env
GOOGLE_WORKSPACE_MCP_URL=http://localhost:8000/mcp
GOOGLE_WORKSPACE_MCP_BEARER_TOKEN=optional_bearer_token
GOOGLE_WORKSPACE_MCP_TIMEOUT_SECONDS=30
```

The Expert agent can then create Drive folders, Docs, and Slides with MCP tools.

### 4. Run

```bash
python main.py
```

---

## Deployment

For 24/7 uptime without running it locally, deploy to [Railway](https://railway.app):

1. Push this repo to GitHub
2. New Project → Deploy from GitHub repo
3. Add your environment variables in the **Variables** tab
4. Railway auto-deploys on every push

The `Procfile` is already included.

---

## Adding a new agent

1. Create `agents/your_agent.py` with an `async def run_your_agent(task: str) -> str` function
2. Add it to `_dispatch` in `bot.py`
3. Add it to the available agents list in the Planner prompt in `agents/planner.py`

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
│   └── memory.py       # Persistent key-value memory
├── graph/
│   └── workflow.py     # LangGraph state graph definition
├── bot.py              # Discord bot, orchestration, progress updates
├── config.py           # Environment variable loading
├── llm.py              # LLM provider factory (OpenAI / Ollama)
├── main.py             # Entry point
└── requirements.txt
```

---

## License

MIT — see [LICENSE](LICENSE).
