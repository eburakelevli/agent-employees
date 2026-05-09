from langchain_core.tools import tool
from ddgs import DDGS
from llm import get_llm
from tools.file_reader import read_file

RESEARCHER_PROMPT = """You are a Research Agent. Your job is to research topics thoroughly and provide clear, concise summaries.

You have access to web search and file reading tools.

Guidelines:
- Use web_search for current information, facts, trends
- Use read_file if the user references a local file path
- Search first, then synthesize
- Be concise but comprehensive
- Cite sources when relevant
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


RESEARCHER_TOOLS = [web_search, read_file]
RESEARCHER_TOOL_MAP = {t.name: t for t in RESEARCHER_TOOLS}


async def run_researcher(message: str) -> str:
    llm = get_llm(temperature=0.3).bind_tools(RESEARCHER_TOOLS)

    messages = [
        {"role": "system", "content": RESEARCHER_PROMPT},
        {"role": "user", "content": message},
    ]

    while True:
        response = await llm.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content

        for tc in response.tool_calls:
            tool_fn = RESEARCHER_TOOL_MAP.get(tc["name"])
            result = tool_fn.invoke(tc["args"]) if tool_fn else f"Unknown tool: {tc['name']}"
            messages.append({
                "role": "tool",
                "content": result,
                "tool_call_id": tc["id"],
            })
