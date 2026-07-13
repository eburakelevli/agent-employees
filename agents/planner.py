import json
from llm import get_llm

PLANNER_PROMPT = """You are a task planner for a multi-agent AI assistant. Break the user's request into an execution plan.

Available agents and their tools:
- researcher: web search, read local files — use for facts, research, reading docs the user provides
- writer: writing content, emails, posts, articles, copy, drafts
- expert: any domain expertise or tool execution — always give a specific role (e.g. "Senior Software Engineer", "Google Workspace Operator", "Product Manager"). Has tools: read files, run Python code, save/recall memory, create Google Drive folders, create Google Docs, create Google Slides, and create Google Sheets via MCP
- summarizer: synthesize multiple outputs into one final cohesive response

Rules:
- The user message may be prefixed with conversation history — use it as context but plan only for the current request at the bottom
- Simple requests (one clear output): 1-2 steps max
- Follow-up or history questions (e.g. "what did I ask?", "expand on that"): use {"agent": "expert", "role": "Conversational Assistant", "task": "..."} — never use "Conversational Assistant" as the agent field
- Complex requests: break into logical sequential steps where later steps build on earlier ones
- For plans with 3+ steps, always end with a summarizer step
- Expert roles must be specific and descriptive, not just "Expert"
- Task descriptions must be specific and actionable
- If the user mentions a file path, include it in the relevant step's task description
- If the user asks to create a Google Sheet/spreadsheet, Google Doc, Slides deck, or Drive folder, use exactly one expert step with role "Google Workspace Operator". The task must explicitly say which MCP tool to use and include the title/name and folder_id. Use folder_id "root" if no folder is provided.
- Never plan a Google Workspace creation request as "Conversational Assistant"; it requires an expert tool call.

The "agent" field must be one of exactly: "researcher", "writer", "expert", "summarizer". Nothing else is valid.

Return ONLY valid JSON in this exact format:
{"steps": [{"agent": "...", "role": null, "task": "..."}, ...]}"""


def _parse_plan_json(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    decoder = json.JSONDecoder()
    data, _ = decoder.raw_decode(text)
    return data


async def create_plan(user_message: str) -> list:
    llm = get_llm(temperature=0, json_mode=True)
    response = await llm.ainvoke([
        {"role": "system", "content": PLANNER_PROMPT},
        {"role": "user", "content": user_message},
    ])
    data = _parse_plan_json(response.content)
    return data.get("steps", [])
