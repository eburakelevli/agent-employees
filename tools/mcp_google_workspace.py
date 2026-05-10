import json
from typing import Optional
from urllib import request, error
from langchain_core.tools import tool

from config import (
    GOOGLE_WORKSPACE_MCP_URL,
    GOOGLE_WORKSPACE_MCP_BEARER_TOKEN,
    GOOGLE_WORKSPACE_MCP_TIMEOUT_SECONDS,
)


def _json_dumps(data: dict) -> bytes:
    return json.dumps(data, separators=(",", ":")).encode("utf-8")


class MCPClient:
    """Minimal JSON-RPC client for streamable HTTP MCP servers."""

    def __init__(self):
        self.url = GOOGLE_WORKSPACE_MCP_URL
        self.token = GOOGLE_WORKSPACE_MCP_BEARER_TOKEN
        self.timeout = GOOGLE_WORKSPACE_MCP_TIMEOUT_SECONDS
        self._id = 1
        self._initialized = False

    def _headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _post(self, payload: dict) -> dict:
        if not self.url:
            raise RuntimeError("GOOGLE_WORKSPACE_MCP_URL is not configured")

        req = request.Request(
            self.url,
            data=_json_dumps(payload),
            headers=self._headers(),
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="ignore").strip()
        except error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"MCP HTTP {e.code}: {body[:500]}") from e
        except Exception as e:
            raise RuntimeError(f"MCP request failed: {e}") from e

        # Some MCP servers stream SSE payloads; keep this parser minimal and robust.
        if raw.startswith("data:"):
            lines = [line[5:].strip() for line in raw.splitlines() if line.startswith("data:")]
            raw = lines[-1] if lines else "{}"

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid MCP JSON response: {raw[:500]}") from e

        if "error" in data:
            message = data["error"].get("message", "Unknown MCP error")
            raise RuntimeError(message)

        return data

    def _rpc(self, method: str, params: Optional[dict] = None) -> dict:
        call_id = self._id
        self._id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": call_id,
            "method": method,
            "params": params or {},
        }
        return self._post(payload)

    def ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._rpc(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "agent-employees", "version": "0.1.0"},
            },
        )
        # Fire-and-forget notification.
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        self._initialized = True

    def call_tool(self, name: str, arguments: dict) -> dict:
        self.ensure_initialized()
        return self._rpc("tools/call", {"name": name, "arguments": arguments})


_MCP = MCPClient()


def _extract_text_result(response: dict) -> str:
    result = response.get("result", {})
    content = result.get("content")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and "text" in item:
                    parts.append(str(item["text"]))
                elif "content" in item:
                    parts.append(str(item["content"]))
        if parts:
            return "\n".join(parts)
    return json.dumps(result, indent=2)


@tool
def mcp_create_drive_folder(folder_name: str, parent_folder_id: str = "root") -> str:
    """Create a Google Drive folder via MCP. Returns the server response text."""
    try:
        response = _MCP.call_tool(
            "create_drive_folder",
            {"folder_name": folder_name, "parent_folder_id": parent_folder_id},
        )
        return _extract_text_result(response)
    except Exception as e:
        return f"MCP create_drive_folder failed: {e}"


@tool
def mcp_create_google_doc(title: str, folder_id: str = "root", content: str = "") -> str:
    """Create a Google Doc file in Drive via MCP. Uses create_drive_file with Google Doc mime type."""
    args = {
        "file_name": title,
        "folder_id": folder_id,
        "mime_type": "application/vnd.google-apps.document",
    }
    if content:
        args["content"] = content

    try:
        response = _MCP.call_tool("create_drive_file", args)
        return _extract_text_result(response)
    except Exception as e:
        return f"MCP create google doc failed: {e}"


@tool
def mcp_create_google_slides(title: str, folder_id: str = "root") -> str:
    """Create a Google Slides file in Drive via MCP. Uses create_drive_file with Slides mime type."""
    try:
        response = _MCP.call_tool(
            "create_drive_file",
            {
                "file_name": title,
                "folder_id": folder_id,
                "mime_type": "application/vnd.google-apps.presentation",
            },
        )
        return _extract_text_result(response)
    except Exception as e:
        return f"MCP create google slides failed: {e}"
