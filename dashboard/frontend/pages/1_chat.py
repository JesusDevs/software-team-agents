import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

st.set_page_config(page_title="Chat — Software Team", page_icon="💬", layout="wide")
st.title("💬 Chat with Supervisor")
st.caption("Send a message to the Supervisor. It will route to the right agent.")

if "pipeline" not in st.session_state:
    st.warning("Go to the **Pipeline** page first to start a run.")
    st.stop()

if not st.session_state.get("started"):
    st.info("Start the pipeline from the **Pipeline** page first.")
    st.stop()

from config.settings import settings
if not settings.has_openai_key():
    st.error("OPENAI_API_KEY not set.")
    st.stop()

# ── conversation display ──────────────────────────────────────────────────────
state = st.session_state.get("graph_state")
messages = state.get("messages", []) if state else []

AGENT_COLORS = {
    "supervisor": "🎯",
    "po_agent":   "📋",
    "ux_agent":   "🎨",
    "architect_agent": "🏗️",
    "dev_agent":  "💻",
    "devops_agent": "🔧",
}

for msg in messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        name = getattr(msg, "name", "") or "agent"
        icon = AGENT_COLORS.get(name, "🤖")
        with st.chat_message("assistant", avatar=icon):
            label = name.replace("_agent", "").upper()
            st.caption(f"**{label}**")
            if msg.content:
                st.markdown(msg.content)
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    with st.expander(f"🔧 Tool call: `{tc['name']}`", expanded=False):
                        st.json(tc.get("args", {}))
    elif isinstance(msg, ToolMessage):
        with st.expander(f"⚙️ Tool result: `{msg.name}`", expanded=False):
            st.code(str(msg.content)[:1000])

# ── HITL panel (inline) ────────────────────────────────────────────────────
if st.session_state.get("pending_interrupt"):
    iv = st.session_state.pending_interrupt
    payload = iv.get("value", iv) if isinstance(iv, dict) else getattr(iv, "value", iv)
    art_name = payload.get("artifact_name", "artifact")

    st.divider()
    st.warning(f"⏸ **Awaiting your approval** for `{art_name}`")
    st.markdown("Go to the **Pipeline** page to review and approve/reject.")

# ── chat input ────────────────────────────────────────────────────────────────
st.divider()
user_input = st.chat_input("Message to Supervisor (e.g., 'Use PostgreSQL not MongoDB')")

if user_input:
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    with st.spinner("Supervisor processing…"):
        try:
            result = st.session_state.pipeline.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
            )
            st.session_state.graph_state = result
            interrupts = result.get("__interrupt__", [])
            st.session_state.pending_interrupt = interrupts[0] if interrupts else None
        except Exception as e:
            st.error(f"Error: {e}")
    st.rerun()
