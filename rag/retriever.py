from rag.store import get_agent_vectorstore
from rag.indexer import index_agent_knowledge


def get_retriever(agent_role: str, k: int = 0):
    """Return a retriever for the agent's knowledge base.
    Auto-indexes any new/changed files before returning.
    """
    import yaml
    from pathlib import Path
    if k == 0:
        cfg = yaml.safe_load(
            (Path(__file__).parent.parent / "config" / "models.yaml").read_text()
        )
        k = cfg.get("rag", {}).get("top_k", 4)
    index_agent_knowledge(agent_role)
    vectorstore = get_agent_vectorstore(agent_role)
    return vectorstore.as_retriever(search_kwargs={"k": k})
