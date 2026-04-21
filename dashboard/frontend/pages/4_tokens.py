import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

st.set_page_config(page_title="Tokens", page_icon="📊", layout="wide")
st.title("📊 Uso de Tokens")
st.caption("Consumo de tokens y costo estimado por agente.")

state = st.session_state.get("graph_state")
if not state:
    st.info("Sin datos aún. Inicia el pipeline desde la página **Pipeline**.")
    st.stop()

token_usage: dict = state.get("token_usage", {})
if not token_usage:
    st.info("Sin datos de tokens aún — el pipeline no ha comenzado o los tokens no están siendo registrados.")
    st.stop()

# Precios aproximados Gemini / OpenAI (por 1K tokens)
INPUT_COST_PER_1K  = 0.005
OUTPUT_COST_PER_1K = 0.015
MINI_INPUT_COST    = 0.000150
MINI_OUTPUT_COST   = 0.000600

MINI_AGENTS = {"supervisor", "devops"}

AGENT_ICONS = {
    "po": "📋", "ux": "🎨", "architect": "🏗️",
    "dev": "💻", "devops": "🔧", "supervisor": "🎯",
}
AGENT_NAMES = {
    "po": "Product Owner", "ux": "Diseñador UX", "architect": "Arquitecto",
    "dev": "Desarrollador", "devops": "DevOps", "supervisor": "Supervisor",
}

total_tokens = 0
total_cost   = 0.0
rows = []

for role, usage in sorted(token_usage.items()):
    inp  = usage.get("input_tokens", 0)
    out  = usage.get("output_tokens", 0)
    tot  = usage.get("total_tokens", inp + out)
    is_mini = role in MINI_AGENTS
    cost = (inp / 1000 * (MINI_INPUT_COST if is_mini else INPUT_COST_PER_1K) +
            out / 1000 * (MINI_OUTPUT_COST if is_mini else OUTPUT_COST_PER_1K))
    total_tokens += tot
    total_cost   += cost
    rows.append({
        "icon": AGENT_ICONS.get(role, "🤖"),
        "role": role,
        "name": AGENT_NAMES.get(role, role.upper()),
        "input": inp, "output": out, "total": tot, "cost": cost,
    })

c1, c2, c3 = st.columns(3)
c1.metric("Tokens totales", f"{total_tokens:,}")
c2.metric("Costo estimado", f"${total_cost:.4f}")
c3.metric("Agentes activos", len(rows))

st.divider()

max_tokens = max((r["total"] for r in rows), default=1)

for row in rows:
    pct = row["total"] / max_tokens if max_tokens else 0
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"{row['icon']} **{row['name']}**")
        st.progress(pct, text=f"{row['total']:,} tokens (entrada: {row['input']:,} / salida: {row['output']:,})")
    with col2:
        st.metric("Costo", f"${row['cost']:.4f}")
    st.divider()

with st.expander("Datos sin procesar"):
    import json
    st.json(token_usage)
