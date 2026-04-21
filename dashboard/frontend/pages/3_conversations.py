import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

st.set_page_config(page_title="Conversaciones", page_icon="👁", layout="wide")
st.title("👁 Conversaciones de Agentes")
st.caption("Historial completo de mensajes incluyendo herramientas y traspasos.")

state = st.session_state.get("graph_state")
if not state:
    st.info("Sin conversación aún. Inicia el pipeline desde la página **Pipeline**.")
    st.stop()

messages = state.get("messages", [])
handoff_log = state.get("handoff_log", [])

col1, col2 = st.columns(2)
show_tool_calls = col1.checkbox("Mostrar llamadas a herramientas", value=True)
show_tool_results = col2.checkbox("Mostrar resultados de herramientas", value=False)

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

st.divider()
st.subheader("Línea de tiempo de traspasos")

if not handoff_log:
    st.info("Sin traspasos registrados aún.")
else:
    for event in handoff_log:
        ts = event.get("timestamp", "")[:19].replace("T", " ")
        frm = event.get("from_agent", "?")
        to  = event.get("to_agent", "?")
        msg = event.get("message", "")
        icon_from = AGENT_ICONS.get(frm, "❓")
        icon_to   = AGENT_ICONS.get(to, "❓")
        name_from = AGENT_NAMES.get(frm, frm)
        name_to   = AGENT_NAMES.get(to, to)
        st.markdown(
            f"`{ts}` &nbsp; {icon_from} **{name_from}** → {icon_to} **{name_to}** &nbsp;— {msg}"
        )

st.divider()
st.subheader("Registro completo de mensajes")

for msg in messages:
    if isinstance(msg, HumanMessage):
        with st.container(border=True):
            st.markdown(f"👤 **Usuario**: {msg.content}")

    elif isinstance(msg, AIMessage):
        name  = getattr(msg, "name", "") or "agent"
        icon  = AGENT_ICONS.get(name, "🤖")
        label = AGENT_NAMES.get(name, name.replace("_", " ").title())
        with st.container(border=True):
            st.markdown(f"{icon} **{label}**")
            if msg.content:
                st.markdown(msg.content[:2000])
            if show_tool_calls and msg.tool_calls:
                for tc in msg.tool_calls:
                    with st.expander(f"🔧 `{tc['name']}({list(tc.get('args', {}).keys())})`"):
                        st.json(tc.get("args", {}))

    elif isinstance(msg, ToolMessage) and show_tool_results:
        with st.container(border=True):
            st.markdown(f"⚙️ **Resultado de herramienta** `{msg.name}`")
            st.code(str(msg.content)[:500])
