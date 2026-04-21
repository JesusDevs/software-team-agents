from langchain_core.tools import tool


def make_search_knowledge_tool(agent_role: str):
    """Factory — returns a search_knowledge tool bound to this agent's vectorstore."""

    @tool
    def search_knowledge(query: str) -> str:
        """Search your personal knowledge base for templates, guidelines, and examples.
        Call this BEFORE generating any artifact to find relevant templates.
        """
        try:
            from rag.retriever import get_retriever
            retriever = get_retriever(agent_role)
            docs = retriever.invoke(query)
            if not docs:
                return f"Base de conocimiento vacía para {agent_role}. Puedes agregar archivos .md en agents/{agent_role}/knowledge/."
            parts = []
            for doc in docs:
                source = doc.metadata.get("source", "unknown")
                parts.append(f"--- [{source}] ---\n{doc.page_content}")
            return "\n\n".join(parts)
        except Exception:
            return f"Base de conocimiento sin documentos para {agent_role}. Usa tu conocimiento interno."

    return search_knowledge
