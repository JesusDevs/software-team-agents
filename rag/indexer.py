import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent.parent
HASH_CACHE_FILE = ROOT_DIR / "rag" / ".index_hashes.json"


def _load_hashes() -> dict:
    if HASH_CACHE_FILE.exists():
        try:
            return json.loads(HASH_CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_hashes(hashes: dict) -> None:
    HASH_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    HASH_CACHE_FILE.write_text(json.dumps(hashes, indent=2))


def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def index_agent_knowledge(agent_role: str, force: bool = False) -> int:
    """Index all .md files in agents/{role}/knowledge/ into the agent's Chroma collection.
    Returns the number of new chunks indexed.
    """
    from config.settings import settings
    if not settings.has_openai_key():
        return 0

    from rag.store import get_agent_vectorstore
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    knowledge_dir = ROOT_DIR / "agents" / agent_role / "knowledge"
    if not knowledge_dir.exists():
        return 0

    md_files = list(knowledge_dir.glob("*.md"))
    if not md_files:
        return 0

    hashes = _load_hashes()
    role_hashes = hashes.get(agent_role, {})
    vectorstore = get_agent_vectorstore(agent_role)

    import yaml
    rag_cfg = yaml.safe_load(
        (ROOT_DIR / "config" / "models.yaml").read_text()
    ).get("rag", {})
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=rag_cfg.get("chunk_size", 800),
        chunk_overlap=rag_cfg.get("chunk_overlap", 100),
        separators=rag_cfg.get("separators", ["\n## ", "\n### ", "\n\n", "\n", " "]),
    )

    indexed = 0
    for md_file in md_files:
        current_hash = _file_hash(md_file)
        if not force and role_hashes.get(md_file.name) == current_hash:
            continue

        content = md_file.read_text(encoding="utf-8")
        docs = splitter.create_documents(
            texts=[content],
            metadatas=[{
                "source": md_file.name,
                "agent": agent_role,
                "hash": current_hash,
                "indexed_at": datetime.now(timezone.utc).isoformat(),
            }],
        )

        # Remove old docs for this file before re-adding
        try:
            vectorstore.delete(where={"source": md_file.name})
        except Exception:
            pass

        vectorstore.add_documents(docs)
        role_hashes[md_file.name] = current_hash
        indexed += len(docs)

    hashes[agent_role] = role_hashes
    _save_hashes(hashes)
    return indexed


def index_all_agents(force: bool = False) -> dict[str, int]:
    """Index knowledge bases for all agents. Returns counts per role."""
    from state.schema import PHASE_ORDER
    results = {}
    for role in PHASE_ORDER:
        results[role] = index_agent_knowledge(role, force=force)
    return results
