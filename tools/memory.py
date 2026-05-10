import json
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
try:
    from langchain_openai import OpenAIEmbeddings
except Exception:
    OpenAIEmbeddings = None

try:
    from pinecone import Pinecone, ServerlessSpec
except Exception:
    Pinecone = None
    ServerlessSpec = None

from config import (
    MEMORY_BACKEND,
    MEMORY_EMBEDDING_MODEL,
    MEMORY_TOP_K,
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_CLOUD,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE,
    PINECONE_REGION,
)

MEMORY_FILE = Path("agent_memory.json")
PINECONE_MANIFEST_FILE = Path("agent_memory_manifest.json")

_pinecone_index = None
_embedding_model = None


def _load() -> dict:
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return {}


def _save(data: dict):
    MEMORY_FILE.write_text(json.dumps(data, indent=2))


def _manifest_load() -> dict[str, str]:
    if PINECONE_MANIFEST_FILE.exists():
        return json.loads(PINECONE_MANIFEST_FILE.read_text())
    return {}


def _manifest_save(data: dict[str, str]):
    PINECONE_MANIFEST_FILE.write_text(json.dumps(data, indent=2))


def _using_pinecone() -> bool:
    return (
        MEMORY_BACKEND == "pinecone"
        and Pinecone is not None
        and OpenAIEmbeddings is not None
        and ServerlessSpec is not None
        and bool(PINECONE_API_KEY)
        and bool(PINECONE_INDEX_NAME)
        and bool(OPENAI_API_KEY)
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _memory_id_for_key(key: str) -> str:
    return f"mem_{sha1(key.encode('utf-8')).hexdigest()}"


def _get_embeddings() -> OpenAIEmbeddings:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = OpenAIEmbeddings(
            model=MEMORY_EMBEDDING_MODEL,
            api_key=OPENAI_API_KEY,
        )
    return _embedding_model


def _ensure_index():
    global _pinecone_index
    if _pinecone_index is not None:
        return _pinecone_index

    pc = Pinecone(api_key=PINECONE_API_KEY)
    listed = pc.list_indexes()
    if hasattr(listed, "names"):
        index_names = set(listed.names())
    else:
        index_names = {ix.name for ix in listed}
    if PINECONE_INDEX_NAME not in index_names:
        dim = len(_get_embeddings().embed_query("memory dimension probe"))
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=dim,
            metric="cosine",
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
        )

    _pinecone_index = pc.Index(PINECONE_INDEX_NAME)
    return _pinecone_index


def _pinecone_upsert(key: str, value: str):
    index = _ensure_index()
    text = f"key: {key}\nvalue: {value}"
    vector = _get_embeddings().embed_query(text)
    memory_id = _memory_id_for_key(key)

    index.upsert(
        vectors=[
            {
                "id": memory_id,
                "values": vector,
                "metadata": {
                    "key": key,
                    "value": value,
                    "created_at": _now_iso(),
                },
            }
        ],
        namespace=PINECONE_NAMESPACE,
    )

    manifest = _manifest_load()
    manifest[key] = memory_id
    _manifest_save(manifest)


def _pinecone_query(query: str) -> dict[str, Any] | None:
    index = _ensure_index()
    vector = _get_embeddings().embed_query(query)

    result = index.query(
        vector=vector,
        top_k=max(1, MEMORY_TOP_K),
        include_metadata=True,
        namespace=PINECONE_NAMESPACE,
    )
    result_data = result.to_dict() if hasattr(result, "to_dict") else (result or {})
    matches = result_data.get("matches", [])
    if not matches:
        return None
    return matches[0]


def _pinecone_delete(key: str) -> bool:
    manifest = _manifest_load()
    memory_id = manifest.get(key)
    if not memory_id:
        return False

    index = _ensure_index()
    index.delete(ids=[memory_id], namespace=PINECONE_NAMESPACE)

    del manifest[key]
    _manifest_save(manifest)
    return True


@tool
def save_memory(key: str, value: str) -> str:
    """Save a piece of information to persistent memory for future conversations. Use a short descriptive key."""
    if _using_pinecone():
        try:
            _pinecone_upsert(key=key, value=value)
            return f"Saved semantic memory (Pinecone): '{key}'"
        except Exception as e:
            return f"Failed to save semantic memory in Pinecone: {e}"

    data = _load()
    data[key] = value
    _save(data)
    return f"Saved memory: '{key}'"


@tool
def recall_memory(key: str) -> str:
    """Recall a memory semantically from the query text (or by exact key if using local memory)."""
    if _using_pinecone():
        try:
            match = _pinecone_query(query=key)
            if not match:
                return f"No semantic memory found for query: '{key}'"
            metadata = match.get("metadata", {}) or {}
            mem_key = metadata.get("key", "unknown")
            mem_value = metadata.get("value", "")
            score = match.get("score")
            return f"[{mem_key}] {mem_value} (score: {score:.3f})" if isinstance(score, (int, float)) else f"[{mem_key}] {mem_value}"
        except Exception as e:
            return f"Failed to query semantic memory in Pinecone: {e}"

    data = _load()
    return data.get(key, f"No memory found for key: '{key}'")


@tool
def list_memories() -> str:
    """List all keys and values currently stored in memory."""
    if _using_pinecone():
        manifest = _manifest_load()
        if not manifest:
            return "No semantic memories stored yet."
        lines = [f"**{k}**: stored in Pinecone" for k in manifest]
        return "\n".join(lines)

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
    if _using_pinecone():
        try:
            deleted = _pinecone_delete(key)
            if not deleted:
                return f"No memory found for key: '{key}'"
            return f"Deleted semantic memory: '{key}'"
        except Exception as e:
            return f"Failed to delete semantic memory from Pinecone: {e}"

    data = _load()
    if key not in data:
        return f"No memory found for key: '{key}'"
    del data[key]
    _save(data)
    return f"Deleted memory: '{key}'"
