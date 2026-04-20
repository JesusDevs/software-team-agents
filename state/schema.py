from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph import MessagesState

PHASE_ORDER = ["po", "ux", "architect", "dev", "devops"]

PHASE_ARTIFACTS = {
    "po":       "01_PRD.md",
    "ux":       "02_UX_SPEC.md",
    "architect":"03_SYSTEM_DESIGN.md",
    "dev":      "04_IMPLEMENTATION_SPEC.md",
    "devops":   "05_DEVOPS_PLAN.md",
}

PHASE_LABELS = {
    "po":       "Product Owner",
    "ux":       "UX Designer",
    "architect":"Software Architect",
    "dev":      "Developer",
    "devops":   "DevOps Engineer",
}


class ArtifactRecord(TypedDict):
    name: str
    content: str
    created_by: str
    version: int
    approved: bool
    feedback_history: list[str]


class AgentTokenUsage(TypedDict):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class HandoffEvent(TypedDict):
    timestamp: str
    from_agent: str
    to_agent: str
    message: str
    task_instructions: str


class ProjectState(MessagesState):
    project_brief: str
    run_id: str
    current_phase: str                          # po | ux | architect | dev | devops | done
    next_agent: str                             # routing decision from supervisor
    task_instructions: str                      # supervisor → active agent
    hitl_feedback: str                          # feedback when HITL rejects
    artifacts: dict[str, ArtifactRecord]        # keyed by filename
    token_usage: dict[str, AgentTokenUsage]     # keyed by agent role
    handoff_log: list[HandoffEvent]             # full handoff history
    error: str                                  # last error if any
