import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="Base de Conocimiento", page_icon="📚", layout="wide")
st.title("📚 Base de Conocimiento")
st.caption("Agrega archivos .md a la carpeta `knowledge/` de cada agente y se indexarán automáticamente.")

ROOT_DIR = Path(__file__).parent.parent.parent
ROLES = ["po", "ux", "architect", "dev", "devops"]
ICONS = {"po": "📋", "ux": "🎨", "architect": "🏗️", "dev": "💻", "devops": "🔧"}
NAMES = {
    "po": "Product Owner", "ux": "Diseñador UX",
    "architect": "Arquitecto", "dev": "Desarrollador", "devops": "DevOps",
}

from llm.models import provider_status
status = provider_status()
rag_note = f"Embeddings activos: **{status.get('embeddings_provider', 'local')}**"
st.info(rag_note)

# ── panel por agente ──────────────────────────────────────────────────────────
for role in ROLES:
    kb_dir = ROOT_DIR / "agents" / role / "knowledge"
    kb_dir.mkdir(parents=True, exist_ok=True)
    md_files = sorted(kb_dir.glob("*.md"))

    with st.expander(
        f"{ICONS[role]} **{NAMES[role]}** — {len(md_files)} archivo(s)",
        expanded=False
    ):
        if not md_files:
            st.info(f"Sin archivos. Agrega archivos .md a `agents/{role}/knowledge/`")
        else:
            for f in md_files:
                col1, col2, col3 = st.columns([4, 1, 1])
                col1.markdown(f"`{f.name}` — {f.stat().st_size:,} bytes")

                if col2.button("👁 Ver", key=f"view_{role}_{f.name}"):
                    st.session_state[f"kb_preview_{role}_{f.name}"] = True

                if col3.button("🔄 Re-indexar", key=f"reindex_{role}_{f.name}"):
                    try:
                        from rag.indexer import index_agent_knowledge
                        n = index_agent_knowledge(role, force=True)
                        st.success(f"Re-indexado {role}: {n} fragmentos")
                    except Exception as e:
                        st.error(f"Error al indexar: {e}")

                preview_key = f"kb_preview_{role}_{f.name}"
                if st.session_state.get(preview_key):
                    st.markdown(f.read_text(encoding="utf-8"))
                    if st.button("Cerrar", key=f"close_{role}_{f.name}"):
                        del st.session_state[preview_key]
                        st.rerun()

        st.divider()

        uploaded = st.file_uploader(
            f"Agregar archivo .md a la base de conocimiento de {NAMES[role]}",
            type=["md"],
            key=f"upload_{role}",
        )
        if uploaded:
            dest = kb_dir / uploaded.name
            dest.write_bytes(uploaded.read())
            st.success(f"Guardado `{uploaded.name}` en `agents/{role}/knowledge/`")
            try:
                from rag.indexer import index_agent_knowledge
                n = index_agent_knowledge(role, force=True)
                st.success(f"Auto-indexado: {n} fragmentos agregados")
            except Exception as e:
                st.warning(f"Archivo guardado pero no indexado: {e}")
            st.rerun()

# ── re-indexar todo ───────────────────────────────────────────────────────────
st.divider()
if st.button("🔄 Re-indexar TODOS los agentes", use_container_width=True):
    try:
        from rag.indexer import index_all_agents
        results = index_all_agents(force=True)
        for role, n in results.items():
            st.write(f"- **{NAMES.get(role, role)}**: {n} fragmentos")
        st.success("¡Listo!")
    except Exception as e:
        st.error(f"Error al indexar: {e}")
