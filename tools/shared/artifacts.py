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


def ensure_artifact_saved(
    role: str,
    artifact_name: str,
    run_id: str,
    messages: list,
) -> None:
    """
    Si el artefacto esperado no existe en disco (el LLM no llamó save_artifact),
    lo guarda automáticamente usando el contenido del último mensaje de IA sustancial.
    Evita que el HITL muestre un artefacto vacío.
    """
    path = _artifacts_path(run_id) / artifact_name
    if path.exists():
        return  # ya fue guardado correctamente

    # Extrae texto plano del content (Gemini devuelve lista de dicts)
    def _extract_text(raw) -> str:
        if isinstance(raw, str):
            return raw
        if isinstance(raw, list):
            parts = []
            for block in raw:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    parts.append(block)
            return "\n".join(parts)
        return str(raw)

    from langchain_core.messages import AIMessage
    content = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            text = _extract_text(msg.content)
            if len(text) > 200:
                content = text
                break

    if content:
        path.write_text(content, encoding="utf-8")
        meta = {
            "name": artifact_name,
            "agent": role,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "size_chars": len(content),
            "path": str(path),
            "auto_saved": True,
        }
        (path.parent / f"{artifact_name}.meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )


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
