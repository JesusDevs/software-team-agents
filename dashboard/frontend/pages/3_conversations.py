import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

st.set_page_config(page_title="Conversations", page_icon="👁", layout="wide")
st.title("👁 Agent Conversations")
st.caption("Full message history including tool calls and handoffs.")

state = st.session_state.get("graph_state")
if not state:
    st.info("No conversation yet. Start the pipeline from the **Pipeline** page.")
    st.stop()

messages = state.get("messages", [])
handoff_log = state.get("handoff_log", [])

# ── filters ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
show_tool_calls = col1.checkbox("Show tool calls", value=True)
show_tool_results = col2.checkbox("Show tool results", value=False)

AGENT_ICONS = {
    "supervisor": "🎯", "po_agent": "📋", "ux_agent": "🎨",
    "architect_agent": "🏗️", "dev_agent": "💻", "devops_agent": "🔧",
}
AGENT_COLORS = {
    "supervisor": "#2563EB", "po_agent": "#7C3AED", "ux_agent": "#DB2777",
    "architect_agent": "#D97706", "dev_agent": "#16A34A", "devops_agent": "#DC2626",
}

st.divider()
st.subheader("Handoff Timeline")

for event in handoff_log:
    ts = event.get("timestamp", "")[:19].replace("T", " ")
    frm = event.get("from_agent", "?")
    to = event.get("to_agent", "?")
    msg = event.get("message", "")
    icon_from = AGENT_ICONS.get(frm, "❓")
    icon_to = AGENT_ICONS.get(to, "❓")
    st.markdown(
        f"`{ts}` &nbsp; {icon_from} **{frm}** → {icon_to} **{to}** &nbsp;— {msg}"
    )

st.divider()
st.subheader("Full Message Log")

for i, msg in enumerate(messages):
    if isinstance(msg, HumanMessage):
        with st.container(border=True):
            st.markdown(f"👤 **Human**: {msg.content}")

    elif isinstance(msg, AIMessage):
        name = getattr(msg, "name", "") or "agent"
        icon = AGENT_ICONS.get(name, "🤖")
        label = name.replace("_", " ").title()
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
            st.markdown(f"⚙️ **Tool result** `{msg.name}`")
            st.code(str(msg.content)[:500])
