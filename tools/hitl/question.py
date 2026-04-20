from langgraph.types import interrupt
from langchain_core.tools import tool


@tool
def ask_question(question: str) -> str:
    """Ask the human a clarifying question when information is missing.
    Use this when you need specific details to proceed (budget, constraints, preferences).
    The human's answer will be returned as a string.
    """
    answer = interrupt({"type": "question", "question": question})
    return str(answer)
