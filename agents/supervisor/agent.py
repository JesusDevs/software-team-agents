from typing import Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from llm.models import get_model_for_agent
from agents.supervisor.prompt import get_system_prompt
from state.schema import ProjectState, PHASE_ORDER, PHASE_ARTIFACTS


class RoutingDecision(BaseModel):
    next_agent: Literal["po", "ux", "architect", "dev", "devops", "done"] = Field(
        description="Which agent to activate next, or 'done' to end the pipeline"
    )
    task_instructions: str = Field(
        description="Detailed instructions for the active agent. Include context from previous artifacts."
    )
    message_to_human: str = Field(
        default="",
        description="Optional message to show the human (e.g., progress update)"
    )


def supervisor_node(state: ProjectState) -> dict:
    phase = state.get("current_phase", "po")
    artifacts = state.get("artifacts", {})
    feedback = state.get("hitl_feedback", "")

    # Determine next agent from current state
    if phase == "done":
        return {"next_agent": "done", "task_instructions": ""}

    # If phase is set and no artifact yet for this phase → run the agent
    artifact_name = PHASE_ARTIFACTS.get(phase, "")
    artifact_exists = artifact_name in artifacts

    # If artifact exists and no feedback → we just came from HITL approval → move to next
    if artifact_exists and not feedback:
        current_idx = PHASE_ORDER.index(phase) if phase in PHASE_ORDER else -1
        if current_idx >= len(PHASE_ORDER) - 1:
            return {"next_agent": "done", "task_instructions": "All phases complete."}
        next_phase = PHASE_ORDER[current_idx + 1]
        phase = next_phase

    # Ask LLM for detailed task instructions
    llm = get_model_for_agent("supervisor").with_structured_output(RoutingDecision)

    context_lines = []
    for art_name, art in artifacts.items():
        preview = art.get("content", "")[:400].replace("\n", " ")
        context_lines.append(f"- {art_name}: {preview}...")

    context_str = "\n".join(context_lines) if context_lines else "No artifacts yet."

    messages = [
        SystemMessage(content=get_system_prompt(state)),
        HumanMessage(content=(
            f"Current phase to execute: {phase}\n"
            f"Feedback from HITL: {feedback or 'none'}\n"
            f"Artifacts so far:\n{context_str}\n\n"
            f"Provide detailed task_instructions for the {phase} agent."
        )),
    ]

    try:
        decision: RoutingDecision = llm.invoke(messages)
        next_agent = phase  # always match current phase
        task_instructions = decision.task_instructions
        human_msg = decision.message_to_human
    except Exception as e:
        next_agent = phase
        task_instructions = f"Execute the {phase} phase for the project: {state.get('project_brief', '')}"
        human_msg = ""

    handoff_log = list(state.get("handoff_log", []))
    handoff_log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from_agent": "supervisor",
        "to_agent": next_agent,
        "message": human_msg or f"Delegating to {next_agent.upper()} agent",
        "task_instructions": task_instructions,
    })

    updates: dict = {
        "next_agent": next_agent,
        "task_instructions": task_instructions,
        "current_phase": next_agent,
        "hitl_feedback": "",
        "handoff_log": handoff_log,
    }
    if human_msg:
        from langchain_core.messages import AIMessage
        updates["messages"] = [AIMessage(content=f"[Supervisor] {human_msg}", name="supervisor")]

    return updates


def route_from_supervisor(state: ProjectState) -> str:
    next_agent = state.get("next_agent", "done")
    if next_agent == "done" or next_agent not in ("po", "ux", "architect", "dev", "devops"):
        return "__end__"
    return f"{next_agent}_agent"
