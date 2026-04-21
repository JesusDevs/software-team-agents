"""
Tests de agentes — valida que cada agente produzca su artefacto MD.
Usa Gemini real (requiere GEMINI_API_KEY en .env).

Ejecutar (todos):
    python -m pytest tests/test_agents.py -v

Ejecutar solo PO (más rápido):
    python -m pytest tests/test_agents.py::test_po_agent_returns_md -v -s

Ejecutar con output en tiempo real:
    python -m pytest tests/test_agents.py -v -s --tb=short
"""
import pytest
import sys
import uuid
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

ROOT = Path(__file__).parent.parent
BRIEF = "App móvil de onboarding de crédito con condiciones claras y botones de acción."


@pytest.fixture(scope="module")
def run_id():
    """ID único de run para estos tests — se limpia al terminar."""
    rid = f"test_{uuid.uuid4().hex[:8]}"
    yield rid
    # Cleanup
    artifacts_dir = ROOT / "artifacts" / rid
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)


@pytest.fixture(scope="module")
def base_state(run_id):
    """Estado base para los tests de agentes."""
    from langchain_core.messages import HumanMessage
    return {
        "messages": [HumanMessage(content=BRIEF)],
        "project_brief": BRIEF,
        "run_id": run_id,
        "current_phase": "po",
        "next_agent": "po",
        "task_instructions": f"Crea el PRD para: {BRIEF}",
        "hitl_feedback": "",
        "artifacts": {},
        "token_usage": {},
        "handoff_log": [],
        "error": "",
    }


def test_po_agent_returns_md(run_id, base_state):
    """PO agent debe guardar 01_PRD.md con contenido en español."""
    from agents.po.agent import po_agent_node
    from langchain_core.runnables import RunnableConfig

    config = RunnableConfig()
    result = po_agent_node(base_state, config)

    # Verifica que retornó artefactos
    artifacts = result.get("artifacts", {})
    assert artifacts, "El agente PO no retornó ningún artefacto en el estado"

    # Verifica el archivo en disco
    md_path = ROOT / "artifacts" / run_id / "01_PRD.md"
    assert md_path.exists(), (
        f"01_PRD.md no fue guardado en {md_path}. "
        f"Artefactos encontrados: {list(artifacts.keys())}"
    )

    content = md_path.read_text(encoding="utf-8")
    assert len(content) > 200, f"01_PRD.md tiene muy poco contenido ({len(content)} chars)"

    # Verifica que está en español (palabras clave)
    content_lower = content.lower()
    spanish_words = ["resumen", "usuario", "historia", "requisito", "problema", "objetivo", "criterio"]
    found = [w for w in spanish_words if w in content_lower]
    assert len(found) >= 2, (
        f"El PRD no parece estar en español. Palabras españolas encontradas: {found}"
    )

    print(f"\n✅ 01_PRD.md guardado ({len(content)} chars)")
    print(f"   Primeras 200 chars: {content[:200]}")


def test_po_agent_updates_state(run_id, base_state):
    """El estado retornado por PO debe tener fase y tokens."""
    from agents.po.agent import po_agent_node
    from langchain_core.runnables import RunnableConfig

    config = RunnableConfig()
    result = po_agent_node(base_state, config)

    assert result.get("current_phase") == "po"
    assert result.get("token_usage", {}).get("po"), "No hay registro de tokens para PO"
    token_data = result["token_usage"]["po"]
    assert token_data["total_tokens"] > 0, "El conteo de tokens es 0"
    print(f"\n   Tokens usados: {token_data['total_tokens']}")


def test_ux_agent_returns_md(run_id):
    """UX agent debe guardar 02_UX_SPEC.md basándose en el PRD existente."""
    from agents.ux.agent import ux_agent_node
    from langchain_core.runnables import RunnableConfig
    from tools.shared.artifacts import load_artifacts_from_fs
    from langchain_core.messages import HumanMessage

    # Usa artefactos del test anterior (01_PRD.md debe existir)
    artifacts = load_artifacts_from_fs(run_id)
    state = {
        "messages": [HumanMessage(content=BRIEF)],
        "project_brief": BRIEF,
        "run_id": run_id,
        "current_phase": "ux",
        "next_agent": "ux",
        "task_instructions": "Crea la especificación UX basándote en el PRD existente.",
        "hitl_feedback": "",
        "artifacts": artifacts,
        "token_usage": {},
        "handoff_log": [],
        "error": "",
    }

    config = RunnableConfig()
    result = ux_agent_node(state, config)

    md_path = ROOT / "artifacts" / run_id / "02_UX_SPEC.md"
    assert md_path.exists(), (
        f"02_UX_SPEC.md no fue guardado. "
        f"Artefactos: {list(result.get('artifacts', {}).keys())}"
    )

    content = md_path.read_text(encoding="utf-8")
    assert len(content) > 200, f"02_UX_SPEC.md tiene muy poco contenido ({len(content)} chars)"
    print(f"\n✅ 02_UX_SPEC.md guardado ({len(content)} chars)")


def test_artifact_ensure_saves_from_gemini_format(run_id):
    """ensure_artifact_saved extrae texto correctamente del formato lista de Gemini."""
    from tools.shared.artifacts import ensure_artifact_saved
    from langchain_core.messages import AIMessage

    # Simula la respuesta de Gemini (lista de dicts)
    gemini_content = [
        {"type": "text", "text": "# Test Artifact\n\nEste es el contenido del artefacto de prueba.\n\n## Sección 1\nContenido de prueba con suficiente texto para superar el mínimo requerido de 200 caracteres para ser guardado automáticamente.\n\n## Sección 2\nMás contenido aquí."}
    ]
    messages = [AIMessage(content=gemini_content)]

    test_name = "test_ensure.md"
    ensure_artifact_saved("test", test_name, run_id, messages)

    test_path = ROOT / "artifacts" / run_id / test_name
    assert test_path.exists(), "ensure_artifact_saved no guardó el archivo con formato Gemini"

    content = test_path.read_text(encoding="utf-8")
    assert "Test Artifact" in content, f"El contenido guardado no contiene el texto esperado: {content[:200]}"
    assert "[{" not in content[:50], "El contenido guardado es la representación de la lista, no el texto"

    print(f"\n✅ ensure_artifact_saved funciona con formato Gemini ({len(content)} chars)")
