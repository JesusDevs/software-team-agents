from langgraph.store.memory import InMemoryStore

_store: InMemoryStore | None = None


def get_store() -> InMemoryStore:
    global _store
    if _store is None:
        _store = InMemoryStore()
    return _store


def reset_store() -> None:
    global _store
    _store = InMemoryStore()
