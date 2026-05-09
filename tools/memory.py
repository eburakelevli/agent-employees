import json
from pathlib import Path
from langchain_core.tools import tool

MEMORY_FILE = Path("agent_memory.json")


def _load() -> dict:
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return {}


def _save(data: dict):
    MEMORY_FILE.write_text(json.dumps(data, indent=2))


@tool
def save_memory(key: str, value: str) -> str:
    """Save a piece of information to persistent memory for future conversations. Use a short descriptive key."""
    data = _load()
    data[key] = value
    _save(data)
    return f"Saved memory: '{key}'"


@tool
def recall_memory(key: str) -> str:
    """Recall a specific memory by its key."""
    data = _load()
    return data.get(key, f"No memory found for key: '{key}'")


@tool
def list_memories() -> str:
    """List all keys and values currently stored in memory."""
    data = _load()
    if not data:
        return "No memories stored yet."
    lines = []
    for k, v in data.items():
        preview = v[:120] + "..." if len(v) > 120 else v
        lines.append(f"**{k}**: {preview}")
    return "\n".join(lines)


@tool
def delete_memory(key: str) -> str:
    """Delete a specific memory by its key."""
    data = _load()
    if key not in data:
        return f"No memory found for key: '{key}'"
    del data[key]
    _save(data)
    return f"Deleted memory: '{key}'"
