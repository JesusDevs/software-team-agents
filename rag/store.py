from pathlib import Path
from functools import lru_cache

ROOT_DIR = Path(__file__).parent.parent
CHROMA_DIR = ROOT_DIR / "rag" / ".chroma"


@lru_cache(maxsize=None)
def get_agent_vectorstore(agent_role: str):
    """Return (or create) the Chroma vectorstore for a specific agent."""
    from langchain_chroma import Chroma
    from llm.models import get_embeddings

    persist_dir = str(CHROMA_DIR / agent_role)
    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=f"knowledge_{agent_role}",
        embedding_function=get_embeddings(),
        persist_directory=persist_dir,
    )
