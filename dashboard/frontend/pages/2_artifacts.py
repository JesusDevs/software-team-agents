import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="Artifacts", page_icon="📄", layout="wide")
st.title("📄 Artifacts")
st.caption("Generated deliverables from each agent.")

run_id = st.session_state.get("run_id", "default")

from config.settings import settings
artifacts_dir = settings.artifacts_dir / run_id

if not artifacts_dir.exists() or not list(artifacts_dir.glob("*.md")):
    st.info("No artifacts yet. Start the pipeline from the **Pipeline** page.")
    st.stop()

md_files = sorted(artifacts_dir.glob("*.md"))
tabs = st.tabs([f.name for f in md_files])

for tab, md_file in zip(tabs, md_files):
    with tab:
        content = md_file.read_text(encoding="utf-8")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"📁 `{md_file}` — {len(content):,} chars")
        with col2:
            st.download_button(
                label="⬇️ Download",
                data=content,
                file_name=md_file.name,
                mime="text/markdown",
                key=f"dl_{md_file.name}",
            )

        # Check for approval status
        state = st.session_state.get("graph_state")
        artifact_record = (state or {}).get("artifacts", {}).get(md_file.name, {})
        if artifact_record.get("approved"):
            st.success("✅ Approved")
        else:
            st.warning("⏳ Pending approval")

        st.markdown("---")
        st.markdown(content)
