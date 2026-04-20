import sys, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from langchain_core.messages import HumanMessage

st.set_page_config(
    page_title="Software Team Agents",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── session state bootstrap ──────────────────────────────────────────────────
def _init_session():
    if "pipeline" not in st.session_state:
        from graph.pipeline import get_pipeline
        from graph.checkpointer import reset_checkpointer
        reset_checkpointer()
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

# ── sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Software Team")
    st.caption(f"Thread: `{st.session_state.thread_id[:8]}…`")
    st.caption(f"Run: `{st.session_state.run_id}`")

    st.divider()
    st.markdown("**Navigation**")
    st.page_link("app.py",                    label="🏠 Pipeline",       icon="🏠")
    st.page_link("pages/1_chat.py",            label="💬 Chat",            icon="💬")
    st.page_link("pages/2_artifacts.py",       label="📄 Artifacts",       icon="📄")
    st.page_link("pages/3_conversations.py",   label="👁 Conversations",    icon="👁")
    st.page_link("pages/4_tokens.py",          label="📊 Tokens",          icon="📊")
    st.page_link("pages/5_knowledge.py",       label="📚 Knowledge Base",   icon="📚")

    st.divider()
    if st.button("🔄 New Run", use_container_width=True):
        from graph.pipeline import reset_pipeline
        from graph.checkpointer import reset_checkpointer
        reset_checkpointer()
        reset_pipeline()
        for key in ["pipeline", "thread_id", "run_id", "graph_state",
                    "pending_interrupt", "started"]:
            st.session_state.pop(key, None)
        st.rerun()

# ── main ─────────────────────────────────────────────────────────────────────
st.title("🤖 Software Team Agents")
st.caption("Multi-agent pipeline: PO → UX → Architect → Dev → DevOps")

from config.settings import settings
from llm.models import provider_status

status = provider_status()
provider = status["active_provider"]

if provider == "none":
    st.error("**No LLM key configured.** Set `OPENAI_API_KEY` or `OPENROUTER_API_KEY` in `.env`")
    st.code("cp .env.example .env\n# Then add your key and restart", language="bash")
    with st.expander("Get a free key via OpenRouter"):
        st.markdown("""
1. Go to [openrouter.ai](https://openrouter.ai) → Sign up (free)
2. Go to **Keys** → Create a new key
3. Add to `.env`:
```
OPENROUTER_API_KEY=sk-or-...
```
4. Free models included: **Llama 3.3 70B**, **DeepSeek R1**, **Gemma 3**
        """)
    st.stop()

# Provider status banner
if provider == "openrouter":
    st.info(f"**Provider: OpenRouter** — model: `{status['llm_model']}`  |  RAG embeddings: {'✅ OpenAI' if status['rag_available'] else '⚠️ disabled (no OpenAI key)'}")
elif provider == "openai":
    st.success(f"**Provider: OpenAI** — model: `gpt-4o`  |  RAG embeddings: ✅")

# ── pipeline status bar ───────────────────────────────────────────────────────
PHASES = ["po", "ux", "architect", "dev", "devops"]
PHASE_LABELS = {"po": "PO", "ux": "UX", "architect": "Architect",
                "dev": "Dev", "devops": "DevOps"}

state = st.session_state.graph_state
current_phase = state.get("current_phase", "") if state else ""
artifacts = state.get("artifacts", {}) if state else {}

cols = st.columns(len(PHASES))
for i, (phase, col) in enumerate(zip(PHASES, cols)):
    art_key = f"0{i+1}_{'PRD' if phase=='po' else phase.upper() if phase in ('ux','dev') else 'SYSTEM_DESIGN' if phase=='architect' else 'DEVOPS_PLAN'}.md"
    # simpler: just check artifacts dict
    has_artifact = any(k.startswith(f"0{i+1}") for k in artifacts)
    is_current = current_phase == phase

    if has_artifact:
        col.success(f"✅ {PHASE_LABELS[phase]}")
    elif is_current:
        col.warning(f"🔄 {PHASE_LABELS[phase]}")
    else:
        col.info(f"⏳ {PHASE_LABELS[phase]}")

st.divider()

# ── start form ────────────────────────────────────────────────────────────────
if not st.session_state.started:
    st.subheader("Start a new project")
    brief = st.text_area(
        "Project brief",
        placeholder="e.g., Build a personal finance app for millennials with expense tracking, budget goals, and investment overview.",
        height=120,
    )
    run_id = st.text_input("Run ID (folder name for artifacts)", value="run_001")

    if st.button("🚀 Start Pipeline", type="primary", use_container_width=True):
        if not brief.strip():
            st.warning("Please enter a project brief.")
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
            with st.spinner("Running PO agent…"):
                try:
                    result = st.session_state.pipeline.invoke(initial_state, config=config)
                    st.session_state.graph_state = result
                    interrupts = result.get("__interrupt__", [])
                    if interrupts:
                        st.session_state.pending_interrupt = interrupts[0]
                except Exception as e:
                    st.error(f"Pipeline error: {e}")
            st.rerun()
else:
    # ── pending HITL ────────────────────────────────────────────────────────
    if st.session_state.pending_interrupt:
        iv = st.session_state.pending_interrupt
        if isinstance(iv, dict):
            payload = iv.get("value", iv)
        else:
            payload = getattr(iv, "value", iv)

        phase = payload.get("phase", "")
        art_name = payload.get("artifact_name", "")
        content = payload.get("content", "")

        st.subheader(f"⏸ HITL — Review `{art_name}`")
        with st.expander("📄 View full artifact", expanded=True):
            st.markdown(content)

        feedback_input = st.text_area("Feedback (optional — leave blank to approve as-is):", key="hitl_feedback_input")

        col1, col2 = st.columns(2)
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        if col1.button("✅ Approve", type="primary", use_container_width=True):
            from langgraph.types import Command
            st.session_state.pending_interrupt = None
            with st.spinner("Resuming pipeline…"):
                try:
                    result = st.session_state.pipeline.invoke(
                        Command(resume={"approved": True}), config=config
                    )
                    st.session_state.graph_state = result
                    interrupts = result.get("__interrupt__", [])
                    st.session_state.pending_interrupt = interrupts[0] if interrupts else None
                except Exception as e:
                    st.error(f"Error: {e}")
            st.rerun()

        if col2.button("❌ Reject & revise", use_container_width=True):
            from langgraph.types import Command
            feedback = st.session_state.get("hitl_feedback_input", "")
            st.session_state.pending_interrupt = None
            with st.spinner("Sending feedback…"):
                try:
                    result = st.session_state.pipeline.invoke(
                        Command(resume={"approved": False, "feedback": feedback}), config=config
                    )
                    st.session_state.graph_state = result
                    interrupts = result.get("__interrupt__", [])
                    st.session_state.pending_interrupt = interrupts[0] if interrupts else None
                except Exception as e:
                    st.error(f"Error: {e}")
            st.rerun()

    elif state and state.get("current_phase") == "done":
        st.success("🎉 Pipeline complete! All 5 deliverables approved.")
        st.balloons()
    else:
        st.info("Pipeline running or waiting. Check the **Chat** page to interact with the Supervisor.")
