"""
LLM + Embeddings factory.

All model configuration lives in config/models.yaml.
Provider is auto-detected from .env (OpenAI > OpenRouter > none).
No code changes needed to switch models — edit models.yaml only.
"""
import yaml
from pathlib import Path
from functools import lru_cache
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from config.settings import settings

_MODELS_PATH = Path(__file__).parent.parent / "config" / "models.yaml"


@lru_cache(maxsize=1)
def _cfg() -> dict:
    with open(_MODELS_PATH) as f:
        return yaml.safe_load(f)


def _provider() -> str:
    if settings.has_openai_key():
        return "openai"
    if settings.has_openrouter_key():
        return "openrouter"
    return "none"


def _model_for_tier(tier: str) -> str:
    provider = _provider()
    if provider == "none":
        return "none"
    return _cfg()["llm_models"][provider][tier]


@lru_cache(maxsize=None)
def get_model_for_agent(role: str) -> ChatOpenAI:
    """Return a ChatOpenAI instance configured for the given agent role.
    Reads tier, temperature, and max_tokens from config/models.yaml.
    Provider is auto-selected from .env keys.
    """
    agent_cfg = _cfg()["agents"].get(role, {})
    tier        = agent_cfg.get("tier", "fast")
    temperature = agent_cfg.get("temperature", 0.3)
    max_tokens  = agent_cfg.get("max_tokens", 2000)
    model       = _model_for_tier(tier)
    provider    = _provider()

    if provider == "openrouter":
        provider_cfg = _cfg()["providers"]["openrouter"]
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.openrouter_api_key,
            base_url=provider_cfg["base_url"],
            streaming=True,
            default_headers=provider_cfg.get("headers", {}),
        )

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.openai_api_key,
        streaming=True,
    )


@lru_cache(maxsize=1)
def get_embeddings():
    """Return the best available embeddings provider.
    Priority: OpenAI (best quality) → local sentence-transformers (free, no key).
    Config lives in config/models.yaml under embeddings.
    """
    emb_cfg = _cfg().get("embeddings", {})

    if settings.has_openai_key():
        model = emb_cfg.get("openai", {}).get("model", "text-embedding-3-small")
        return OpenAIEmbeddings(model=model, api_key=settings.openai_api_key)

    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        local_cfg = emb_cfg.get("local", {})
        return HuggingFaceEmbeddings(
            model_name=local_cfg.get("model", "sentence-transformers/all-MiniLM-L6-v2"),
            model_kwargs={"device": local_cfg.get("device", "cpu")},
            encode_kwargs={"normalize_embeddings": True},
        )
    except ImportError:
        return OpenAIEmbeddings(model="text-embedding-3-small", api_key="sk-placeholder")


def provider_status() -> dict:
    """Quick summary of active providers. Used by the dashboard banner."""
    provider = _provider()
    cfg = _cfg()
    has_local_emb = True  # sentence-transformers always available as fallback
    emb_label = (
        f"OpenAI ({cfg['embeddings']['openai']['model']})"
        if settings.has_openai_key()
        else f"local ({cfg['embeddings']['local']['model'].split('/')[-1]})"
    )
    return {
        "active_provider":     provider,
        "openai_available":    settings.has_openai_key(),
        "openrouter_available": settings.has_openrouter_key(),
        "rag_available":       True,
        "embeddings_provider": emb_label,
        "llm_strong_model":    _model_for_tier("strong"),
        "llm_fast_model":      _model_for_tier("fast"),
    }
