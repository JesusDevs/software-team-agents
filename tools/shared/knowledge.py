from langchain_core.tools import tool
from config.settings import settings


def make_search_knowledge_tool(agent_role: str):
    """Factory — returns a search_knowledge tool bound to this agent's vectorstore."""

    @tool
    def search_knowledge(query: str) -> str:
        """Search your personal knowledge base for templates, guidelines, and examples.
        Call this BEFORE generating any artifact to find relevant templates.
        """
        if not settings.has_openai_key():
            return "Knowledge base unavailable (OPENAI_API_KEY not set)."
        try:
            from rag.retriever import get_retriever
            retriever = get_retriever(agent_role)
            docs = retriever.invoke(query)
            if not docs:
                return "No relevant documents found in knowledge base."
            parts = []
            for doc in docs:
                source = doc.metadata.get("source", "unknown")
                parts.append(f"--- [{source}] ---\n{doc.page_content}")
            return "\n\n".join(parts)
        except Exception as e:
            return f"Knowledge base error: {e}"

    return search_knowledge
