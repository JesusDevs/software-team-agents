import yaml
from pathlib import Path
from functools import lru_cache
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from config.settings import settings

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "agents.yaml"


def _load_agent_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=None)
def get_model_for_agent(role: str) -> ChatOpenAI:
    cfg = _load_agent_config().get(role, {})
    return ChatOpenAI(
        model=cfg.get("model", "gpt-4o-mini"),
        temperature=cfg.get("temperature", 0.3),
        max_tokens=cfg.get("max_tokens", 2000),
        api_key=settings.openai_api_key,
        streaming=True,
    )


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    cfg = _load_agent_config().get("embeddings", {})
    return OpenAIEmbeddings(
        model=cfg.get("model", "text-embedding-3-small"),
        api_key=settings.openai_api_key,
    )
