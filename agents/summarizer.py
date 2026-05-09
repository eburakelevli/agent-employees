from llm import get_llm

SUMMARIZER_PROMPT = """You are a Synthesis Agent. You receive outputs from multiple specialized agents and combine them into one clear, cohesive final response.

Guidelines:
- Integrate all inputs — don't just list them separately
- Remove redundancy, keep the best insights from each agent
- Format for Discord (use headers and bullets where they add clarity)
- Be concise but complete"""


async def run_summarizer(task: str) -> str:
    llm = get_llm(temperature=0.3)
    response = await llm.ainvoke([
        {"role": "system", "content": SUMMARIZER_PROMPT},
        {"role": "user", "content": task},
    ])
    return response.content
