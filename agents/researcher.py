from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from duckduckgo_search import DDGS
from config import OPENAI_API_KEY, OPENAI_MODEL

RESEARCHER_PROMPT = """You are a Research Agent. Your job is to research topics thoroughly and provide clear, concise summaries.

You have access to a web search tool. Use it when you need current information.

Guidelines:
- Search first, then synthesize
- Be concise but comprehensive
- Cite what you found when relevant
- If the user's question is simple, don't over-research it
- Format your response for Discord (use markdown sparingly, keep it readable)"""


@tool
def web_search(query: str) -> str:
    """Search the web for current information. Use this for any research task."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return "No results found."
        formatted = []
        for r in results:
            formatted.append(f"**{r['title']}**\n{r['body']}\nSource: {r['href']}")
        return "\n\n".join(formatted)
    except Exception as e:
        return f"Search failed: {str(e)}"


async def run_researcher(message: str) -> str:
    """Run the researcher agent on a message."""
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.3,
    ).bind_tools([web_search])

    messages = [
        {"role": "system", "content": RESEARCHER_PROMPT},
        {"role": "user", "content": message},
    ]

    # Agent loop: keep going until no more tool calls
    while True:
        response = await llm.ainvoke(messages)
        messages.append(response)

        # If no tool calls, we're done
        if not response.tool_calls:
            return response.content

        # Execute each tool call
        for tc in response.tool_calls:
            if tc["name"] == "web_search":
                result = web_search.invoke(tc["args"])
                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tc["id"],
                })
