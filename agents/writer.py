from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

WRITER_PROMPT = """You are a Writing Agent. Your job is to draft content based on the user's request.

You can write:
- Social media posts (LinkedIn, Instagram, Twitter)
- Emails (professional, casual)
- Articles, blog posts
- Copy, taglines, captions
- Any other written content

Guidelines:
- Match the tone the user asks for (professional, casual, witty, etc.)
- Keep it concise unless asked for long-form
- Format for Discord (use markdown sparingly)
- Ask clarifying questions if the request is too vague
- Provide one strong draft, not multiple options (unless asked)"""


async def run_writer(message: str) -> str:
    """Run the writer agent on a message."""
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.7,
    )

    response = await llm.ainvoke([
        {"role": "system", "content": WRITER_PROMPT},
        {"role": "user", "content": message},
    ])

    return response.content
