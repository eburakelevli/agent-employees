import json
from pathlib import Path

HISTORY_FILE = Path("conversation_history.json")
MAX_EXCHANGES = 10  # per user


def _load() -> dict:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {}


def _save(data: dict):
    HISTORY_FILE.write_text(json.dumps(data, indent=2))


def get_history(user_id: int) -> list[dict]:
    return _load().get(str(user_id), [])


def add_exchange(user_id: int, question: str, answer: str):
    data = _load()
    uid = str(user_id)
    if uid not in data:
        data[uid] = []
    data[uid].append({"q": question, "a": answer})
    data[uid] = data[uid][-MAX_EXCHANGES:]
    _save(data)


def format_history(user_id: int) -> str:
    history = get_history(user_id)
    if not history:
        return ""
    lines = [
        "The following is the actual conversation history with this user.",
        "Use it to answer any follow-up or reference questions (e.g. 'what did I ask before?', 'expand on that').\n"
    ]
    for i, exchange in enumerate(history, 1):
        answer_preview = exchange["a"][:400] + "..." if len(exchange["a"]) > 400 else exchange["a"]
        lines.append(f"[Exchange {i}]")
        lines.append(f"User asked: {exchange['q']}")
        lines.append(f"You answered: {answer_preview}\n")
    return "\n".join(lines)
