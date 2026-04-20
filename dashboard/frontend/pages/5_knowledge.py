import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="Knowledge Base", page_icon="📚", layout="wide")
st.title("📚 Knowledge Base")
st.caption("Drop .md files into an agent's knowledge/ folder and they'll be indexed automatically.")

ROOT_DIR = Path(__file__).parent.parent.parent
ROLES = ["po", "ux", "architect", "dev", "devops"]
ICONS = {"po": "📋", "ux": "🎨", "architect": "🏗️", "dev": "💻", "devops": "🔧"}

from config.settings import settings

if not settings.has_openai_key():
    st.warning("OPENAI_API_KEY not set — RAG indexing is disabled. Knowledge files still show here.")

# ── per-agent panels ──────────────────────────────────────────────────────────
for role in ROLES:
    kb_dir = ROOT_DIR / "agents" / role / "knowledge"
    kb_dir.mkdir(parents=True, exist_ok=True)
    md_files = sorted(kb_dir.glob("*.md"))

    with st.expander(f"{ICONS[role]} **{role.upper()}** — {len(md_files)} file(s)", expanded=False):
        if not md_files:
            st.info(f"No files yet. Add .md files to `agents/{role}/knowledge/`")
        else:
            for f in md_files:
                col1, col2, col3 = st.columns([4, 1, 1])
                col1.markdown(f"`{f.name}` — {f.stat().st_size:,} bytes")

                if col2.button("👁 View", key=f"view_{role}_{f.name}"):
                    st.session_state[f"kb_preview_{role}_{f.name}"] = True

                if col3.button("🔄 Re-index", key=f"reindex_{role}_{f.name}"):
                    if settings.has_openai_key():
                        from rag.indexer import index_agent_knowledge
                        n = index_agent_knowledge(role, force=True)
                        st.success(f"Re-indexed {role}: {n} chunks")
                    else:
                        st.warning("OpenAI key required for indexing.")

                preview_key = f"kb_preview_{role}_{f.name}"
                if st.session_state.get(preview_key):
                    st.markdown(f.read_text(encoding="utf-8"))
                    if st.button("Close", key=f"close_{role}_{f.name}"):
                        del st.session_state[preview_key]
                        st.rerun()

        st.divider()

        # Upload new file
        uploaded = st.file_uploader(
            f"Add a new .md file to {role.upper()} knowledge base",
            type=["md"],
            key=f"upload_{role}",
        )
        if uploaded:
            dest = kb_dir / uploaded.name
            dest.write_bytes(uploaded.read())
            st.success(f"Saved `{uploaded.name}` to `agents/{role}/knowledge/`")
            if settings.has_openai_key():
                from rag.indexer import index_agent_knowledge
                n = index_agent_knowledge(role, force=True)
                st.success(f"Auto-indexed: {n} chunks added")
            st.rerun()

# ── global re-index ───────────────────────────────────────────────────────────
st.divider()
if st.button("🔄 Re-index ALL agents", use_container_width=True):
    if settings.has_openai_key():
        from rag.indexer import index_all_agents
        results = index_all_agents(force=True)
        for role, n in results.items():
            st.write(f"- **{role}**: {n} chunks")
        st.success("Done!")
    else:
        st.warning("OPENAI_API_KEY required for indexing.")
