"""
Persistent checkpointer using SQLite so pipeline state survives restarts.
DB lives at data/checkpoints.db (gitignored).
"""
import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

_DB_PATH = Path(__file__).parent.parent / "data" / "checkpoints.db"
_checkpointer: SqliteSaver | None = None
_conn: sqlite3.Connection | None = None


def get_checkpointer() -> SqliteSaver:
    global _checkpointer, _conn
    if _checkpointer is None:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        _checkpointer = SqliteSaver(_conn)
    return _checkpointer


def reset_checkpointer() -> None:
    """Force re-open. Does NOT delete existing checkpoint data."""
    global _checkpointer, _conn
    if _conn:
        try:
            _conn.close()
        except Exception:
            pass
    _checkpointer = None
    _conn = None


def list_threads() -> list[dict]:
    """Return saved threads: [{thread_id, last_updated}]"""
    if not _DB_PATH.exists():
        return []
    try:
        con = sqlite3.connect(str(_DB_PATH))
        cur = con.cursor()
        cur.execute("""
            SELECT thread_id, MAX(thread_ts)
            FROM checkpoints
            GROUP BY thread_id
            ORDER BY MAX(thread_ts) DESC
        """)
        rows = cur.fetchall()
        con.close()
        return [{"thread_id": r[0], "last_updated": r[1]} for r in rows]
    except Exception:
        return []
