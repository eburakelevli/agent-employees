from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

SUMMARIZER_PROMPT = """You are a Synthesis Agent. You receive outputs from multiple specialized agents and combine them into one clear, cohesive final response.

Guidelines:
- Integrate all inputs — don't just list them separately
- Remove redundancy, keep the best insights from each agent
- Format for Discord (use headers and bullets where they add clarity)
- Be concise but complete"""


async def run_summarizer(task: str) -> str:
    llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.3)
    response = await llm.ainvoke([
        {"role": "system", "content": SUMMARIZER_PROMPT},
        {"role": "user", "content": task},
    ])
    return response.content
