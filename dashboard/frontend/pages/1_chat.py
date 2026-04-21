import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

st.set_page_config(page_title="Chat — Equipo IA", page_icon="💬", layout="wide")
st.title("💬 Chat con el Supervisor")
st.caption("Envía un mensaje al Supervisor. Él lo redirige al agente correcto.")

if "pipeline" not in st.session_state:
    st.warning("Ve a la página **Pipeline** primero para iniciar un run.")
    st.stop()

if not st.session_state.get("started"):
    st.info("Inicia el pipeline desde la página **Pipeline** primero.")
    st.stop()

from llm.models import provider_status
status = provider_status()
if status["active_provider"] == "none":
    st.error("No hay proveedor LLM configurado. Agrega una clave API en `.env`.")
    st.stop()

# ── historial de conversación ─────────────────────────────────────────────────
state = st.session_state.get("graph_state")
messages = state.get("messages", []) if state else []

AGENT_ICONS = {
    "supervisor":      "🎯",
    "po_agent":        "📋",
    "ux_agent":        "🎨",
    "architect_agent": "🏗️",
    "dev_agent":       "💻",
    "devops_agent":    "🔧",
}
AGENT_NAMES = {
    "supervisor":      "Supervisor",
    "po_agent":        "Product Owner",
    "ux_agent":        "Diseñador UX",
    "architect_agent": "Arquitecto",
    "dev_agent":       "Desarrollador",
    "devops_agent":    "DevOps",
}

for msg in messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        name = getattr(msg, "name", "") or "agent"
        icon = AGENT_ICONS.get(name, "🤖")
        label = AGENT_NAMES.get(name, name.replace("_agent", "").upper())
        with st.chat_message("assistant", avatar=icon):
            st.caption(f"**{label}**")
            if msg.content:
                st.markdown(msg.content)
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    with st.expander(f"🔧 Herramienta: `{tc['name']}`", expanded=False):
                        st.json(tc.get("args", {}))
    elif isinstance(msg, ToolMessage):
        with st.expander(f"⚙️ Resultado de herramienta: `{msg.name}`", expanded=False):
            st.code(str(msg.content)[:1000])

# ── aviso de HITL pendiente ───────────────────────────────────────────────────
if st.session_state.get("pending_interrupt"):
    iv = st.session_state.pending_interrupt
    payload = iv.get("value", iv) if isinstance(iv, dict) else getattr(iv, "value", iv)
    art_name = payload.get("artifact_name", "artefacto")
    st.divider()
    st.warning(f"⏸ **Esperando tu aprobación** de `{art_name}`. Ve a la página **Pipeline** para revisar.")

# ── input de chat ─────────────────────────────────────────────────────────────
st.divider()
user_input = st.chat_input("Mensaje al Supervisor (ej: 'Usa PostgreSQL en vez de MongoDB')")

if user_input:
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    with st.spinner("El Supervisor está procesando…"):
        def _get_pending_interrupt(pipeline, config):
            try:
                from state.schema import PHASE_ARTIFACTS
                snapshot = pipeline.get_state(config)
                if not snapshot or not snapshot.values:
                    return None
                if snapshot.tasks:
                    for task in snapshot.tasks:
                        if hasattr(task, "interrupts") and task.interrupts:
                            iv = task.interrupts[0]
                            val = iv.value if hasattr(iv, "value") else iv
                            return {"value": val}
                next_nodes = snapshot.next or []
                if "hitl_gate" in next_nodes:
                    vals = snapshot.values
                    phase = vals.get("current_phase", "")
                    art_name = PHASE_ARTIFACTS.get(phase, "")
                    artifact = vals.get("artifacts", {}).get(art_name, {})
                    return {"value": {
                        "phase": phase,
                        "artifact_name": art_name,
                        "content": artifact.get("content", ""),
                    }}
            except Exception:
                pass
            return None

        try:
            result = st.session_state.pipeline.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
            )
            st.session_state.graph_state = result
            st.session_state.pending_interrupt = _get_pending_interrupt(
                st.session_state.pipeline, config
            )
        except Exception as e:
            st.error(f"Error: {e}")
    st.rerun()
