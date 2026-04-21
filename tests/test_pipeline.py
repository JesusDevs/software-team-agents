"""
Test de pipeline completo (smoke test).
Ejecuta el pipeline hasta el primer interrupt (HITL después de PO).

Ejecutar:
    python -m pytest tests/test_pipeline.py -v -s
    python -m pytest tests/test_pipeline.py::test_pipeline_po_to_hitl -v -s
"""
import pytest
import sys
import uuid
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

ROOT = Path(__file__).parent.parent
BRIEF = "Crea una landing page para una startup de inteligencia artificial."


@pytest.fixture(scope="module")
def run_id():
    rid = f"smoke_{uuid.uuid4().hex[:8]}"
    yield rid
    artifacts_dir = ROOT / "artifacts" / rid
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    # Limpia checkpoint del test
    db_path = ROOT / "data" / "checkpoints.db"
    # No borramos el DB global — solo anotamos que el thread fue de test


def test_pipeline_compiles():
    """El pipeline debe compilar sin errores."""
    from graph.pipeline import create_pipeline
    pipeline = create_pipeline()
    nodes = list(pipeline.nodes.keys())
    expected = ["supervisor", "po_agent", "ux_agent", "architect_agent", "dev_agent", "devops_agent", "hitl_gate"]
    for node in expected:
        assert node in nodes, f"Nodo '{node}' faltante en el pipeline. Nodos: {nodes}"
    print(f"\n✅ Pipeline compilado con nodos: {nodes}")


def test_pipeline_checkpointer_is_sqlite():
    """El checkpointer debe ser SQLite (no MemorySaver)."""
    from graph.pipeline import create_pipeline
    from langgraph.checkpoint.sqlite import SqliteSaver
    pipeline = create_pipeline()
    assert isinstance(pipeline.checkpointer, SqliteSaver), (
        f"Se esperaba SqliteSaver pero se obtuvo: {type(pipeline.checkpointer).__name__}"
    )
    print(f"\n✅ Checkpointer: SqliteSaver (persistente)")


def test_pipeline_po_to_hitl(run_id):
    """
    El pipeline debe correr desde PO hasta el primer HITL.
    Valida: PO genera MD, se guarda en disco, el pipeline pausa en hitl_gate.
    """
    from graph.pipeline import create_pipeline
    from langchain_core.messages import HumanMessage

    pipeline = create_pipeline()
    thread_id = f"test_{uuid.uuid4().hex}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "messages": [HumanMessage(content=BRIEF)],
        "project_brief": BRIEF,
        "run_id": run_id,
        "current_phase": "po",
        "next_agent": "po",
        "task_instructions": "",
        "hitl_feedback": "",
        "artifacts": {},
        "token_usage": {},
        "handoff_log": [],
        "error": "",
    }

    result = pipeline.invoke(initial_state, config=config)

    # 1. Verifica que el pipeline pausó en hitl_gate
    snapshot = pipeline.get_state(config)
    next_nodes = list(snapshot.next or [])
    assert "hitl_gate" in next_nodes, (
        f"El pipeline no se pausó en hitl_gate. Próximos nodos: {next_nodes}. "
        f"Fase actual: {result.get('current_phase')}"
    )

    # 2. Verifica que 01_PRD.md fue guardado
    md_path = ROOT / "artifacts" / run_id / "01_PRD.md"
    assert md_path.exists(), f"01_PRD.md no fue generado en {md_path}"

    content = md_path.read_text(encoding="utf-8")
    assert len(content) > 100, f"01_PRD.md tiene muy poco contenido: {len(content)} chars"

    # 3. Verifica que los artefactos están en el estado
    artifacts = result.get("artifacts", {})
    assert any("PRD" in k or "prd" in k.lower() or k.startswith("01") for k in artifacts), (
        f"No hay artefacto PRD en el estado. Artefactos: {list(artifacts.keys())}"
    )

    # 4. Verifica tokens
    token_usage = result.get("token_usage", {})
    assert "po" in token_usage, "No hay registro de tokens para el agente PO"
    assert token_usage["po"]["total_tokens"] > 0, "Tokens = 0"

    print(f"\n✅ Pipeline PO → HITL exitoso")
    print(f"   Fase: {result.get('current_phase')}")
    print(f"   Artefactos: {list(artifacts.keys())}")
    print(f"   Tokens PO: {token_usage.get('po', {}).get('total_tokens', 0)}")
    print(f"   PRD ({len(content)} chars):\n   {content[:200]}...")


def test_pipeline_state_persists_after_restart(run_id):
    """El estado debe persistir entre reinicios del pipeline (SQLite checkpoint)."""
    from graph.pipeline import create_pipeline
    from langchain_core.messages import HumanMessage

    thread_id = f"persist_{uuid.uuid4().hex}"
    config = {"configurable": {"thread_id": thread_id}}

    # Primera invocación
    pipeline1 = create_pipeline()
    initial_state = {
        "messages": [HumanMessage(content=BRIEF)],
        "project_brief": BRIEF,
        "run_id": run_id,
        "current_phase": "po",
        "next_agent": "po",
        "task_instructions": "",
        "hitl_feedback": "",
        "artifacts": {},
        "token_usage": {},
        "handoff_log": [],
        "error": "",
    }
    pipeline1.invoke(initial_state, config=config)

    # Segunda invocación — pipeline nuevo, mismo thread_id
    from graph.pipeline import reset_pipeline
    reset_pipeline()
    pipeline2 = create_pipeline()

    snapshot = pipeline2.get_state(config)
    assert snapshot.values, "El estado no persiste entre reinicios del pipeline"
    assert snapshot.values.get("project_brief") == BRIEF, "El brief no se recuperó del checkpoint"

    print(f"\n✅ Estado persistido en SQLite y recuperado correctamente")
    print(f"   Brief recuperado: '{snapshot.values.get('project_brief', '')[:60]}...'")
