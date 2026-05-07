from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

AGENT_OPTIONS = {
    "researcher": "Handles research, fact-finding, summarization, trend analysis, comparisons",
    "writer": "Handles writing tasks: emails, posts, captions, articles, copy, drafts",
}

ROUTER_PROMPT = """You are a router. Your job is to read the user's message and decide which agent should handle it.

Available agents:
{agents_list}

Reply with ONLY the agent name (one word, lowercase). Nothing else."""


def build_agents_list() -> str:
    return "\n".join(f"- {name}: {desc}" for name, desc in AGENT_OPTIONS.items())


async def route_message(message: str) -> str:
    """Returns the name of the agent that should handle this message."""
    llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0)
    prompt = ROUTER_PROMPT.format(agents_list=build_agents_list())

    response = await llm.ainvoke([
        {"role": "system", "content": prompt},
        {"role": "user", "content": message},
    ])

    agent_name = response.content.strip().lower()

    # Fallback if the LLM returns something unexpected
    if agent_name not in AGENT_OPTIONS:
        agent_name = "researcher"

    return agent_name
