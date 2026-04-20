import threading
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
_observer = None


class _KnowledgeHandler:
    def dispatch(self, event):
        if hasattr(event, "src_path") and str(event.src_path).endswith(".md"):
            path = Path(event.src_path)
            parts = path.parts
            try:
                agents_idx = parts.index("agents")
                role = parts[agents_idx + 1]
                from rag.indexer import index_agent_knowledge
                n = index_agent_knowledge(role, force=True)
                if n > 0:
                    print(f"[RAG] Re-indexed {role} knowledge: {path.name} ({n} chunks)")
            except (ValueError, IndexError):
                pass


def start_watcher() -> None:
    """Start filesystem watcher for agents/*/knowledge/ in a background thread."""
    global _observer
    from config.settings import settings
    if not settings.has_openai_key():
        return
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class Handler(FileSystemEventHandler, _KnowledgeHandler):
            pass

        agents_dir = ROOT_DIR / "agents"
        _observer = Observer()
        _observer.schedule(Handler(), path=str(agents_dir), recursive=True)
        t = threading.Thread(target=_observer.start, daemon=True)
        t.start()
    except ImportError:
        pass


def stop_watcher() -> None:
    global _observer
    if _observer:
        _observer.stop()
        _observer = None
