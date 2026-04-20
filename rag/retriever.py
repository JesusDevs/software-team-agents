from rag.store import get_agent_vectorstore
from rag.indexer import index_agent_knowledge


def get_retriever(agent_role: str, k: int = 4):
    """Return a retriever for the agent's knowledge base.
    Auto-indexes any new/changed files before returning.
    """
    index_agent_knowledge(agent_role)
    vectorstore = get_agent_vectorstore(agent_role)
    return vectorstore.as_retriever(search_kwargs={"k": k})
