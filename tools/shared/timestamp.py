from datetime import datetime, timezone
from langchain_core.tools import tool


@tool
def current_timestamp() -> str:
    """Returns the current UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
