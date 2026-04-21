from langgraph.types import interrupt, Command
from langgraph.graph import END
from state.schema import ProjectState, PHASE_ORDER, PHASE_ARTIFACTS


def hitl_gate(state: ProjectState) -> Command:
    """HITL node: interrupts the graph and waits for human approval of the current artifact."""
    from config.settings import settings

    phase = state.get("current_phase", "")
    artifact_name = PHASE_ARTIFACTS.get(phase, "")
    artifact = state.get("artifacts", {}).get(artifact_name, {})
    content = artifact.get("content", "")

    # Fallback: leer del disco si el estado no tiene el contenido
    if not content and artifact_name:
        run_id = state.get("run_id", "default")
        disk_path = settings.artifacts_dir / run_id / artifact_name
        if disk_path.exists():
            content = disk_path.read_text(encoding="utf-8")

    decision = interrupt({
        "phase": phase,
        "artifact_name": artifact_name,
        "content": content,
        "message": f"Revisa el {artifact_name} del agente {phase.upper()}.",
    })

    approved: bool = decision.get("approved", False)
    feedback: str = decision.get("feedback", "")

    if approved:
        current_idx = PHASE_ORDER.index(phase) if phase in PHASE_ORDER else -1
        if current_idx >= len(PHASE_ORDER) - 1:
            return Command(goto=END, update={"current_phase": "done", "hitl_feedback": ""})
        next_phase = PHASE_ORDER[current_idx + 1]
        return Command(goto="supervisor", update={
            "current_phase": next_phase,
            "hitl_feedback": "",
        })
    else:
        return Command(goto=f"{phase}_agent", update={
            "hitl_feedback": feedback or "Please revise the work.",
            "current_phase": phase,
        })
