import sys, uuid, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from langchain_core.messages import HumanMessage

st.set_page_config(
    page_title="Equipo de Software IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── registro de sesiones en disco ─────────────────────────────────────────────
_REGISTRY = Path(__file__).parent.parent.parent / "data" / "sessions.json"

def _load_registry() -> dict:
    if _REGISTRY.exists():
        try:
            return json.loads(_REGISTRY.read_text())
        except Exception:
            return {}
    return {}

def _save_session(thread_id: str, run_id: str, brief: str, phase: str) -> None:
    _REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    registry = _load_registry()
    registry[thread_id] = {
        "run_id": run_id,
        "brief": brief[:120],
        "phase": phase,
        "updated": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    }
    _REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False))

def _delete_session(thread_id: str) -> None:
    registry = _load_registry()
    registry.pop(thread_id, None)
    _REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False))

# ── detección de interrupts (LangGraph 1.1.x) ─────────────────────────────────
def _get_pending_interrupt(pipeline, config):
    """
    Detecta si el grafo está pausado en hitl_gate.
    LangGraph 1.1.x puede no poblar tasks.interrupts, así que usamos
    snapshot.next para detectar la pausa y reconstruimos el payload
    directamente desde el estado guardado.
    """
    try:
        from state.schema import PHASE_ARTIFACTS
        snapshot = pipeline.get_state(config)
        if not snapshot or not snapshot.values:
            return None

        # Enfoque 1: tasks.interrupts (LangGraph >= 0.2 con interrupt())
        if snapshot.tasks:
            for task in snapshot.tasks:
                if hasattr(task, "interrupts") and task.interrupts:
                    iv = task.interrupts[0]
                    # Puede ser objeto Interrupt o dict
                    val = iv.value if hasattr(iv, "value") else iv
                    return {"value": val}

        # Enfoque 2: si hitl_gate es el próximo nodo, reconstruimos el payload
        next_nodes = snapshot.next or []
        if "hitl_gate" in next_nodes:
            vals  = snapshot.values
            phase = vals.get("current_phase", "")
            art_name = PHASE_ARTIFACTS.get(phase, "")
            artifact = vals.get("artifacts", {}).get(art_name, {})
            return {"value": {
                "phase":         phase,
                "artifact_name": art_name,
                "content":       artifact.get("content", ""),
                "message":       f"Revisa el artefacto {art_name} del agente {phase.upper()}.",
            }}
    except Exception:
        pass
    return None

# ── inicialización de session state ──────────────────────────────────────────
def _init_session():
    if "pipeline" not in st.session_state:
        from graph.pipeline import get_pipeline
        st.session_state.pipeline = get_pipeline()

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    if "run_id" not in st.session_state:
        st.session_state.run_id = "default"

    if "graph_state" not in st.session_state:
        st.session_state.graph_state = None

    if "pending_interrupt" not in st.session_state:
        st.session_state.pending_interrupt = None

    if "started" not in st.session_state:
        st.session_state.started = False

    if "watcher_started" not in st.session_state:
        from rag.watcher import start_watcher
        start_watcher()
        st.session_state.watcher_started = True

_init_session()

# ── restaurar sesión desde checkpoint ────────────────────────────────────────
def _restore_from_checkpoint(thread_id: str) -> None:
    config = {"configurable": {"thread_id": thread_id}}
    try:
        pipeline = st.session_state.pipeline
        snapshot = pipeline.get_state(config)
        if snapshot and snapshot.values:
            st.session_state.graph_state = snapshot.values
            st.session_state.started = True
            st.session_state.pending_interrupt = _get_pending_interrupt(pipeline, config)
    except Exception as e:
        st.warning(f"No se pudo restaurar el estado: {e}")

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Equipo de Software")
    st.caption(f"Sesión: `{st.session_state.thread_id[:8]}…`")
    st.caption(f"Run: `{st.session_state.run_id}`")

    st.divider()
    st.markdown("**Navegación**")
    st.page_link("app.py",                    label="🏠 Pipeline")
    st.page_link("pages/1_chat.py",            label="💬 Chat")
    st.page_link("pages/2_artifacts.py",       label="📄 Artefactos")
    st.page_link("pages/3_conversations.py",   label="👁 Conversaciones")
    st.page_link("pages/4_tokens.py",          label="📊 Tokens")
    st.page_link("pages/5_knowledge.py",       label="📚 Base de Conocimiento")

    st.divider()

    # ── sesiones guardadas ────────────────────────────────────────────────────
    registry = _load_registry()
    if registry:
        st.markdown("**💾 Sesiones guardadas**")
        for tid, meta in sorted(registry.items(), key=lambda x: x[1].get("updated",""), reverse=True):
            label = f"{meta['run_id']} · {meta['phase']} · {meta['updated'][5:16]}"
            col_r, col_x = st.columns([5, 1])
            if col_r.button(label, key=f"restore_{tid}", use_container_width=True):
                st.session_state.thread_id = tid
                st.session_state.run_id = meta["run_id"]
                st.session_state.graph_state = None
                st.session_state.pending_interrupt = None
                st.session_state.started = False
                _restore_from_checkpoint(tid)
                st.rerun()
            if col_x.button("✕", key=f"del_{tid}"):
                _delete_session(tid)
                st.rerun()
        st.divider()

    if st.button("🆕 Nuevo Run", use_container_width=True):
        from graph.pipeline import reset_pipeline
        reset_pipeline()
        for key in ["pipeline", "thread_id", "run_id", "graph_state",
                    "pending_interrupt", "started"]:
            st.session_state.pop(key, None)
        st.rerun()

# ── encabezado ────────────────────────────────────────────────────────────────
st.title("🤖 Equipo de Software IA")
st.caption("Pipeline multi-agente: PO → UX → Arquitecto → Dev → DevOps")

from llm.models import provider_status

status = provider_status()
provider = status["active_provider"]

if provider == "none":
    st.error("**No hay clave LLM configurada.** Agrega una en `.env` y reinicia.")
    st.stop()

emb = status.get("embeddings_provider", "desconocido")
strong = status.get("llm_strong_model", "")
banner_map = {
    "gemini":     ("🟢", "Gemini"),
    "openai":     ("🟢", "OpenAI"),
    "kimi":       ("🟡", "Kimi"),
    "openrouter": ("🟡", "OpenRouter"),
}
icon, label = banner_map.get(provider, ("⚪", provider.title()))
st.info(f"{icon} **LLM: {label}** `{strong}`  ·  **Embeddings:** {emb}")

# ── barra de progreso del pipeline ────────────────────────────────────────────
PHASES = ["po", "ux", "architect", "dev", "devops"]
PHASE_LABELS = {"po": "PO", "ux": "UX", "architect": "Arquitecto",
                "dev": "Dev", "devops": "DevOps"}

state = st.session_state.graph_state
current_phase = state.get("current_phase", "") if state else ""
artifacts = state.get("artifacts", {}) if state else {}

cols = st.columns(len(PHASES))
for i, (phase, col) in enumerate(zip(PHASES, cols)):
    has_artifact = any(k.startswith(f"0{i+1}") for k in artifacts)
    is_current = current_phase == phase
    if has_artifact:
        col.success(f"✅ {PHASE_LABELS[phase]}")
    elif is_current:
        col.warning(f"🔄 {PHASE_LABELS[phase]}")
    else:
        col.info(f"⏳ {PHASE_LABELS[phase]}")

st.divider()

# ── formulario de inicio ──────────────────────────────────────────────────────
if not st.session_state.started:
    st.subheader("Iniciar un nuevo proyecto")
    brief = st.text_area(
        "Brief del proyecto",
        placeholder="Ej: Crear una app de finanzas personales para millennials con seguimiento de gastos, metas de ahorro y vista de inversiones.",
        height=120,
    )
    run_id = st.text_input("ID del run (nombre de carpeta para los artefactos)", value="run_001")

    if st.button("🚀 Iniciar Pipeline", type="primary", use_container_width=True):
        if not brief.strip():
            st.warning("Por favor ingresa un brief del proyecto.")
        else:
            st.session_state.run_id = run_id or "run_001"
            st.session_state.started = True

            initial_state = {
                "messages": [HumanMessage(content=brief)],
                "project_brief": brief,
                "run_id": run_id or "run_001",
                "current_phase": "po",
                "next_agent": "po",
                "task_instructions": "",
                "hitl_feedback": "",
                "artifacts": {},
                "token_usage": {},
                "handoff_log": [],
                "error": "",
            }

            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            with st.spinner("Ejecutando agente PO…"):
                try:
                    result = st.session_state.pipeline.invoke(initial_state, config=config)
                    st.session_state.graph_state = result
                    st.session_state.pending_interrupt = _get_pending_interrupt(
                        st.session_state.pipeline, config
                    )
                    _save_session(
                        st.session_state.thread_id,
                        st.session_state.run_id,
                        brief,
                        result.get("current_phase", "po"),
                    )
                except Exception as e:
                    st.error(f"Error en el pipeline: {e}")
            st.rerun()
else:
    # ── panel HITL ────────────────────────────────────────────────────────────
    if st.session_state.pending_interrupt:
        iv = st.session_state.pending_interrupt
        if isinstance(iv, dict):
            payload = iv.get("value", iv)
        else:
            payload = getattr(iv, "value", iv)

        phase    = payload.get("phase", "")
        art_name = payload.get("artifact_name", "")
        content  = payload.get("content", "")

        st.subheader(f"⏸ Revisión humana — `{art_name}`")
        with st.expander("📄 Ver artefacto completo", expanded=True):
            st.markdown(content)

        feedback_input = st.text_area(
            "Feedback (opcional — déjalo vacío para aprobar tal cual):",
            key="hitl_feedback_input"
        )

        col1, col2 = st.columns(2)
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        if col1.button("✅ Aprobar", type="primary", use_container_width=True):
            from langgraph.types import Command
            st.session_state.pending_interrupt = None
            with st.spinner("Reanudando pipeline…"):
                try:
                    result = st.session_state.pipeline.invoke(
                        Command(resume={"approved": True}), config=config
                    )
                    st.session_state.graph_state = result
                    st.session_state.pending_interrupt = _get_pending_interrupt(
                        st.session_state.pipeline, config
                    )
                    _save_session(
                        st.session_state.thread_id,
                        st.session_state.run_id,
                        state.get("project_brief", "") if state else "",
                        result.get("current_phase", phase),
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
            st.rerun()

        if col2.button("❌ Rechazar y revisar", use_container_width=True):
            from langgraph.types import Command
            feedback = st.session_state.get("hitl_feedback_input", "")
            st.session_state.pending_interrupt = None
            with st.spinner("Enviando feedback…"):
                try:
                    result = st.session_state.pipeline.invoke(
                        Command(resume={"approved": False, "feedback": feedback}), config=config
                    )
                    st.session_state.graph_state = result
                    st.session_state.pending_interrupt = _get_pending_interrupt(
                        st.session_state.pipeline, config
                    )
                    _save_session(
                        st.session_state.thread_id,
                        st.session_state.run_id,
                        state.get("project_brief", "") if state else "",
                        result.get("current_phase", phase),
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
            st.rerun()

    elif state and state.get("current_phase") == "done":
        st.success("🎉 ¡Pipeline completo! Los 5 entregables fueron aprobados.")
        st.balloons()
    else:
        st.info("Pipeline en ejecución. Verifica la página de **Chat** para interactuar con el Supervisor.")
