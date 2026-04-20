import yaml
from pathlib import Path
from functools import lru_cache
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from config.settings import settings, OPENROUTER_BASE_URL

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "agents.yaml"

# Free models available on OpenRouter (no billing required)
OPENROUTER_FREE_MODELS = {
    "strong":  "meta-llama/llama-3.3-70b-instruct:free",   # PO, UX, Architect, Dev
    "fast":    "meta-llama/llama-3.2-3b-instruct:free",    # Supervisor, DevOps
    "reason":  "deepseek/deepseek-r1:free",                 # optional reasoning
}


def _load_agent_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _make_llm(model: str, temperature: float, max_tokens: int) -> ChatOpenAI:
    provider = settings.active_provider()

    if provider == "openrouter":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.openrouter_api_key,
            base_url=OPENROUTER_BASE_URL,
            streaming=True,
            default_headers={
                "HTTP-Referer": "https://github.com/software-team-agents",
                "X-Title": "Software Team Agents",
            },
        )

    # default: OpenAI
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.openai_api_key,
        streaming=True,
    )


@lru_cache(maxsize=None)
def get_model_for_agent(role: str) -> ChatOpenAI:
    cfg = _load_agent_config().get(role, {})
    provider = settings.active_provider()

    if provider == "openrouter":
        # Use free OpenRouter models — strong for complex agents, fast for simple ones
        fast_roles = {"supervisor", "devops"}
        model = OPENROUTER_FREE_MODELS["fast"] if role in fast_roles else OPENROUTER_FREE_MODELS["strong"]
    else:
        model = cfg.get("model", "gpt-4o-mini")

    return _make_llm(
        model=model,
        temperature=cfg.get("temperature", 0.3),
        max_tokens=cfg.get("max_tokens", 2000),
    )


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    """Embeddings always use OpenAI (OpenRouter doesn't provide embeddings API).
    Falls back gracefully if key is missing — RAG will be disabled.
    """
    cfg = _load_agent_config().get("embeddings", {})
    api_key = settings.openai_api_key if settings.has_openai_key() else "sk-placeholder"
    return OpenAIEmbeddings(
        model=cfg.get("model", "text-embedding-3-small"),
        api_key=api_key,
    )


def provider_status() -> dict:
    """Returns a summary of which providers are active."""
    provider = settings.active_provider()
    return {
        "active_provider": provider,
        "openai_available": settings.has_openai_key(),
        "openrouter_available": settings.has_openrouter_key(),
        "rag_available": settings.has_openai_key(),  # embeddings need OpenAI
        "llm_model": (
            OPENROUTER_FREE_MODELS["strong"] if provider == "openrouter"
            else "gpt-4o" if provider == "openai"
            else "none"
        ),
    }
