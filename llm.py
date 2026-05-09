from config import LLM_PROVIDER, OPENAI_API_KEY, OPENAI_MODEL, OLLAMA_BASE_URL, OLLAMA_MODEL


def get_llm(temperature: float = 0.7, json_mode: bool = False):
    """Return a configured LLM based on LLM_PROVIDER env var."""
    if LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=temperature,
            format="json" if json_mode else None,
        )

    from langchain_openai import ChatOpenAI
    kwargs = {}
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    return ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=temperature,
        **kwargs,
    )
