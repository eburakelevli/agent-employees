# Agent Employees

A multi-agent Discord bot that acts as your personal AI team. Give it a task and it plans the work, delegates to the right specialists, and shows you live progress — all inside Discord.

Built with [LangGraph](https://github.com/langchain-ai/langgraph), [LangChain](https://github.com/langchain-ai/langchain), and [discord.py](https://github.com/Rapptz/discord.py).

---

## How it works

Every message goes through a **Planner** that breaks the task into steps and assigns each one to a specialist agent. Agents pass context to one another so each step builds on the last.

```
You: @agent-employees build a content strategy for my AI startup

Planner creates:
  ⚙️ 1. RESEARCHER      — current AI startup trends
  ⏳ 2. RESEARCHER      — competitor landscape
  ⏳ 3. EXPERT: Marketing Strategist — content strategy
  ⏳ 4. SUMMARIZER      — final synthesis

[STEP 1 — RESEARCHER] ...
[STEP 2 — RESEARCHER] ...
[STEP 3 — EXPERT: Marketing Strategist] ...
[FINAL SYNTHESIS] ...
3,241 tokens · $0.00048
```

---

## Agents

| Agent | Role |
|-------|------|
| **Planner** | Breaks any task into steps, assigns agents, coordinates context passing |
| **Researcher** | Web search, fact-finding, trend analysis, current events |
| **Writer** | Emails, blog posts, social media copy, articles, drafts |
| **Expert** | Any domain expertise — the Planner assigns a specific role (e.g. Senior Software Engineer, Senior AI Engineer, Product Manager) |
| **Summarizer** | Synthesizes outputs from multiple agents into a final response |

---

## Usage

**Let the Planner decide (recommended for complex tasks):**
```
@agent-employees review this system architecture: ...
@agent-employees write a cold outreach email to a VC firm
@agent-employees what are the best index funds for a UK investor?
```

**Target an agent directly (faster for simple tasks):**
```
@agent-employees writer: write a tweet about multi-agent AI
@agent-employees researcher: latest news on OpenAI
```

Token usage is shown after every response so you can track API costs.

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

Edit `.env`:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

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
2. Add it to the `_dispatch` function in `bot.py`
3. Add it to the available agents list in the Planner prompt in `agents/planner.py`

---

## Project structure

```
agent-employees/
├── agents/
│   ├── expert.py       # Generic expert — any role assigned by the Planner
│   ├── planner.py      # Creates execution plans from user tasks
│   ├── researcher.py   # Web search via DuckDuckGo + LLM synthesis
│   ├── summarizer.py   # Synthesizes multi-agent outputs
│   └── writer.py       # Content and copy writing
├── graph/
│   └── workflow.py     # LangGraph state graph definition
├── bot.py              # Discord bot, orchestration, progress updates
├── config.py           # Environment variable loading
├── main.py             # Entry point
└── requirements.txt
```

---

## License

MIT — see [LICENSE](LICENSE).
