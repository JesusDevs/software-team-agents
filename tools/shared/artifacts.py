import json
from datetime import datetime, timezone
from pathlib import Path
from langchain_core.tools import tool
from config.settings import settings


def _artifacts_path(run_id: str) -> Path:
    p = settings.artifacts_dir / run_id
    p.mkdir(parents=True, exist_ok=True)
    return p


@tool
def save_artifact(name: str, content: str, agent: str = "", run_id: str = "default") -> str:
    """Save a generated artifact (markdown, json, yaml) to the artifacts directory.
    Always call this after generating a deliverable.
    Returns a confirmation with the saved path.
    """
    path = _artifacts_path(run_id)
    (path / name).write_text(content, encoding="utf-8")

    meta = {
        "name": name,
        "agent": agent,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "size_chars": len(content),
        "path": str(path / name),
    }
    (path / f"{name}.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return f"Artifact '{name}' saved ({len(content)} chars) at {path / name}"


@tool
def read_artifact(name: str, run_id: str = "default") -> str:
    """Read a previously saved artifact by filename."""
    path = _artifacts_path(run_id) / name
    if not path.exists():
        return f"Artifact '{name}' not found in run '{run_id}'."
    return path.read_text(encoding="utf-8")


@tool
def list_artifacts(run_id: str = "default") -> str:
    """List all artifacts generated in this run."""
    path = _artifacts_path(run_id)
    files = [f.name for f in sorted(path.glob("*.md")) + sorted(path.glob("*.json"))
             if not f.name.endswith(".meta.json")]
    if not files:
        return "No artifacts yet."
    return "\n".join(files)


def load_artifacts_from_fs(run_id: str) -> dict:
    """Load all artifacts from filesystem into a dict for state."""
    path = _artifacts_path(run_id)
    result = {}
    for f in sorted(path.glob("*.md")):
        content = f.read_text(encoding="utf-8")
        meta_file = path / f"{f.name}.meta.json"
        agent = ""
        if meta_file.exists():
            try:
                agent = json.loads(meta_file.read_text()).get("agent", "")
            except Exception:
                pass
        result[f.name] = {
            "name": f.name,
            "content": content,
            "created_by": agent,
            "version": 1,
            "approved": False,
            "feedback_history": [],
        }
    return result
