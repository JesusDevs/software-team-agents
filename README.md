# Software Team Agents

Multi-agent pipeline that simulates a complete software team using **LangGraph** + **LangSmith** + **Streamlit**.

Five specialized agents collaborate sequentially under a **Supervisor**, with a **Human-in-the-Loop (HITL)** gate after every deliverable. Each agent has its own **RAG knowledge base** that auto-indexes when you drop `.md` files into its `knowledge/` folder.

```
PO → UX → Architect → Dev → DevOps
     [HITL gate between each phase]
```

---

## Architecture at a Glance

```
software-team-agents/
│
├── agents/                  ← One folder per role
│   ├── po/
│   │   ├── agent.py         ← ReAct loop + tool execution
│   │   ├── prompt.py        ← System prompt (reads state for context)
│   │   ├── tools.py         ← Tool list for this agent
│   │   ├── schema.py        ← Pydantic output schemas
│   │   └── knowledge/       ← Drop .md files here → auto-indexed into RAG
│   ├── ux/        (same structure)
│   ├── architect/ (same structure)
│   ├── dev/       (same structure)
│   ├── devops/    (same structure)
│   └── supervisor/
│       ├── agent.py         ← Structured-output routing (RoutingDecision)
│       └── prompt.py
│
├── tools/
│   ├── shared/
│   │   ├── artifacts.py     ← save_artifact / read_artifact / list_artifacts
│   │   ├── search.py        ← web_search (DuckDuckGo, no key needed)
│   │   ├── timestamp.py     ← current_timestamp
│   │   └── knowledge.py     ← make_search_knowledge_tool(role) factory
│   └── hitl/
│       ├── approval.py      ← hitl_gate node — interrupt() + Command routing
│       └── question.py      ← ask_question tool for agents to query human
│
├── state/
│   ├── schema.py            ← ProjectState (extends MessagesState) + type defs
│   └── store.py             ← InMemoryStore singleton
│
├── graph/
│   ├── pipeline.py          ← StateGraph assembly + compile (THE MAIN GRAPH)
│   └── checkpointer.py      ← MemorySaver singleton
│
├── llm/
│   └── models.py            ← get_model_for_agent(role) + get_embeddings()
│
├── rag/
│   ├── indexer.py           ← Scan knowledge/, detect changes by MD5, chunk+embed
│   ├── store.py             ← Chroma vectorstore per agent (persisted in .chroma/)
│   ├── retriever.py         ← get_retriever(role) — auto-indexes before returning
│   └── watcher.py           ← watchdog filesystem watcher for live re-indexing
│
├── dashboard/frontend/
│   ├── app.py               ← Home: pipeline status + start form + HITL approvals
│   └── pages/
│       ├── 1_chat.py        ← Chat with Supervisor (routes to any agent)
│       ├── 2_artifacts.py   ← Rendered MD viewer + download per artifact
│       ├── 3_conversations.py ← Full message log + handoff timeline
│       ├── 4_tokens.py      ← Token usage + cost estimate per agent
│       └── 5_knowledge.py   ← Knowledge base manager (view, upload, re-index)
│
├── config/
│   ├── settings.py          ← Pydantic Settings (reads .env)
│   └── agents.yaml          ← Model, temperature, max_tokens per agent
│
├── main.py                  ← CLI entry point (headless mode)
├── requirements.txt
└── .env.example
```

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USER/software-team-agents.git
cd software-team-agents
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-...          # Required — for LLM + embeddings
LANGCHAIN_API_KEY=ls__...      # Optional — activates LangSmith tracing
LANGCHAIN_TRACING_V2=true      # Set to true to enable LangSmith
LANGCHAIN_PROJECT=software-team-agents
```

### 3. Run the dashboard

```bash
streamlit run dashboard/frontend/app.py
# Opens http://localhost:8501
```

### 4. Or run headless (CLI)

```bash
python3 main.py --brief "Build a personal finance app" --run-id my_run
# Use --auto-approve to skip all HITL gates
python3 main.py --brief "..." --auto-approve
```

---

## How the pipeline works

1. **You enter a project brief** in the dashboard.
2. **Supervisor** analyzes the brief and generates task instructions for the first agent (PO).
3. **PO Agent** runs a ReAct loop: searches the web, consults its knowledge base, and generates `01_PRD.md`.
4. **HITL Gate** pauses the graph and shows you the artifact. You approve or reject with feedback.
5. If approved → Supervisor activates the next agent (UX).
6. If rejected → Supervisor re-activates the same agent with your feedback.
7. Cycle repeats through UX → Architect → Dev → DevOps.
8. When all 5 artifacts are approved, the pipeline ends.

---

## Agent Knowledge Base (RAG)

Each agent has a `knowledge/` folder. Files there are automatically vectorized with OpenAI embeddings and stored in a per-agent ChromaDB collection.

```bash
# Add a template to PO's knowledge base
echo "# My Jira Template..." > agents/po/knowledge/my_jira_template.md
# → auto-indexed in < 1 second (watchdog detects the change)
# → PO will use it in the next run via search_knowledge("jira template")
```

Pre-loaded knowledge files:
| Agent | Files |
|-------|-------|
| PO | `prd_template.md`, `user_story_format.md`, `linear_jira_templates.md` |
| UX | `design_principles.md` |
| Architect | `adr_template.md`, `architecture_patterns.md` |
| Dev | `coding_standards.md` |
| DevOps | `ci_cd_templates.md` |

---

## Dashboard Pages

| Page | What you see |
|------|-------------|
| 🏠 Pipeline | Status bar per phase, start form, HITL approval panel |
| 💬 Chat | Chat with Supervisor — ask questions, redirect agents, get updates |
| 📄 Artifacts | Rendered markdown for each generated deliverable + download |
| 👁 Conversations | Full message log: every LLM call, tool call, handoff event |
| 📊 Tokens | Token usage and estimated cost per agent |
| 📚 Knowledge Base | View, upload, and re-index knowledge files per agent |

---

## Customizing agents

### Change a system prompt
Edit `agents/{role}/prompt.py` — the `get_system_prompt(state)` function.

### Change the model or temperature
Edit `config/agents.yaml`:
```yaml
architect:
  model: gpt-4o        # or gpt-4o-mini, gpt-4-turbo
  temperature: 0.2
  max_tokens: 5000
```

### Add a tool to an agent
1. Create or import the tool in `agents/{role}/tools.py`
2. Add it to the `TOOLS` list in `agents/{role}/agent.py`

### Add knowledge to an agent
Drop a `.md` file into `agents/{role}/knowledge/`. That's it.

---

## LangSmith Tracing

Set `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` in `.env`.
Every run will appear at [smith.langchain.com](https://smith.langchain.com) under the project `software-team-agents`.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent framework | LangGraph 0.2+ |
| LLM | OpenAI GPT-4o / GPT-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |
| Vector store | ChromaDB (per-agent, persisted) |
| Observability | LangSmith |
| Dashboard | Streamlit |
| Search | DuckDuckGo (no API key) |
| Config | Pydantic Settings |
| State | LangGraph MessagesState + checkpointer |
