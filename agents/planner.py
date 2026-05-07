import json
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

PLANNER_PROMPT = """You are a task planner for a multi-agent AI assistant. Break the user's request into an execution plan.

Available agents:
- researcher: web search, fact-finding, current events, trends, data gathering
- writer: writing content, emails, posts, articles, copy, drafts
- expert: any domain expertise — always give a specific role (e.g. "Senior Software Engineer", "Senior AI Engineer", "Product Manager", "Data Scientist", "Marketing Strategist")
- summarizer: synthesize multiple outputs into one final cohesive response

Rules:
- Simple requests (one clear output): 1-2 steps max
- Complex requests: break into logical sequential steps where later steps build on earlier ones
- For plans with 3+ steps, always end with a summarizer step
- Expert roles must be specific and descriptive, not just "Expert"
- Task descriptions must be specific and actionable

Return ONLY valid JSON in this exact format:
{"steps": [{"agent": "...", "role": null, "task": "..."}, ...]}"""


async def create_plan(user_message: str) -> list:
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    response = await llm.ainvoke([
        {"role": "system", "content": PLANNER_PROMPT},
        {"role": "user", "content": user_message},
    ])
    data = json.loads(response.content)
    return data.get("steps", [])
