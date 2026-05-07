# Agent Employees - Discord Bot with LangGraph

A multi-agent Discord bot powered by LangGraph and OpenAI. Each agent is an "employee" with a specific role.

## Current Agents
- **Router** - Automatically routes your message to the right agent
- **Researcher** - Searches the web and summarizes findings
- **Writer** - Drafts content, emails, social posts, etc.

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create a Discord Bot
1. Go to https://discord.com/developers/applications
2. Click "New Application" → name it → go to "Bot" tab
3. Click "Reset Token" → copy the token
4. Enable "Message Content Intent" under Privileged Gateway Intents
5. Go to OAuth2 → URL Generator → select "bot" scope → select "Send Messages", "Read Message History" permissions
6. Copy the generated URL → open it to invite the bot to your server

### 3. Set environment variables
```bash
cp .env.example .env
# Edit .env with your keys
```

### 4. Run
```bash
python main.py
```

## Usage in Discord
Just message in any channel the bot can see:
- "Research the latest trends in agentic AI" → routes to Researcher
- "Write me a LinkedIn post about my new project" → routes to Writer
- "What agent are you?" → routes to best match

## Adding New Agents
1. Create a new file in `agents/` following the pattern in `researcher.py`
2. Register it in `graph/workflow.py`
3. Add it to the router's options in `agents/router.py`
