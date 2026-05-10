from llm import get_llm
from tools.file_reader import read_file
from tools.code_runner import run_python
from tools.memory import save_memory, recall_memory, list_memories, delete_memory
from tools.mcp_google_workspace import (
    mcp_create_drive_folder,
    mcp_create_google_doc,
    mcp_create_google_slides,
)

EXPERT_TOOLS = [
    read_file,
    run_python,
    save_memory,
    recall_memory,
    list_memories,
    delete_memory,
    mcp_create_drive_folder,
    mcp_create_google_doc,
    mcp_create_google_slides,
]
EXPERT_TOOL_MAP = {t.name: t for t in EXPERT_TOOLS}

EXPERT_PROMPT_TEMPLATE = """You are a {role}. You are highly experienced and provide expert-level analysis and solutions.

You have access to tools:
- read_file: read any local file (pass the full path)
- run_python: execute Python code for calculations, analysis, or data processing
- save_memory / recall_memory / list_memories / delete_memory: persist information across conversations (recall can be semantic if Pinecone backend is enabled)
- mcp_create_drive_folder: create a Google Drive folder via MCP
- mcp_create_google_doc: create a Google Doc in Drive via MCP
- mcp_create_google_slides: create a Google Slides deck in Drive via MCP

Guidelines:
- Use tools when they genuinely help — don't use them for things you can answer directly
- Be specific and actionable, not generic
- Format for Discord (markdown sparingly, keep it readable)
- Be concise unless the task requires depth"""


async def run_expert(role: str, task: str) -> str:
    llm = get_llm(temperature=0.3).bind_tools(EXPERT_TOOLS)

    messages = [
        {"role": "system", "content": EXPERT_PROMPT_TEMPLATE.format(role=role)},
        {"role": "user", "content": task},
    ]

    while True:
        response = await llm.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content

        for tc in response.tool_calls:
            tool_fn = EXPERT_TOOL_MAP.get(tc["name"])
            result = tool_fn.invoke(tc["args"]) if tool_fn else f"Unknown tool: {tc['name']}"
            messages.append({
                "role": "tool",
                "content": result,
                "tool_call_id": tc["id"],
            })
