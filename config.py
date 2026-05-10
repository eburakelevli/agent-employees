import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# LLM provider — "openai", "claude", or "ollama"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Ollama — set OLLAMA_MODEL to whichever model you have pulled (e.g. llama3.2, mistral, qwen2.5)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Claude (Anthropic)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# Memory backend (optional Pinecone semantic memory)
MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "local").lower()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "default")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
MEMORY_EMBEDDING_MODEL = os.getenv("MEMORY_EMBEDDING_MODEL", "text-embedding-3-small")
MEMORY_TOP_K = int(os.getenv("MEMORY_TOP_K", "3"))

# Google Workspace MCP (optional)
GOOGLE_WORKSPACE_MCP_URL = os.getenv("GOOGLE_WORKSPACE_MCP_URL", "")
GOOGLE_WORKSPACE_MCP_BEARER_TOKEN = os.getenv("GOOGLE_WORKSPACE_MCP_BEARER_TOKEN", "")
GOOGLE_WORKSPACE_MCP_TIMEOUT_SECONDS = int(os.getenv("GOOGLE_WORKSPACE_MCP_TIMEOUT_SECONDS", "30"))
