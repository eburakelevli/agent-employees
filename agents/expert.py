from llm import get_llm


async def run_expert(role: str, task: str) -> str:
    prompt = f"""You are a {role}. You are highly experienced and provide expert-level analysis and solutions.

Guidelines:
- Be specific and actionable, not generic
- Format for Discord (markdown sparingly, keep it readable)
- Be concise unless the task requires depth"""

    llm = get_llm(temperature=0.3)
    response = await llm.ainvoke([
        {"role": "system", "content": prompt},
        {"role": "user", "content": task},
    ])
    return response.content
