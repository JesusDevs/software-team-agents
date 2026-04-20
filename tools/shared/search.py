from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Search the web for up-to-date information on a topic.
    Use this to research domains, competitors, best practices, or any factual data.
    """
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        return DuckDuckGoSearchRun().run(query)
    except Exception as e:
        return f"Search unavailable ({e}). Use your training knowledge to proceed."
