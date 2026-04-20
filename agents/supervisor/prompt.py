from state.schema import ProjectState, PHASE_ORDER, PHASE_LABELS


def get_system_prompt(state: ProjectState) -> str:
    phase = state.get("current_phase", "po")
    feedback = state.get("hitl_feedback", "")
    artifacts = state.get("artifacts", {})
    brief = state.get("project_brief", "")

    completed = [p for p in PHASE_ORDER if state.get("artifacts", {}).get(
        f"0{PHASE_ORDER.index(p)+1}_{p.upper()}.md") or
        any(k.startswith(f"0{PHASE_ORDER.index(p)+1}") for k in artifacts)]

    return f"""You are the Supervisor of a software development team.
Your job is to orchestrate the team to deliver a complete software project.

## Project Brief
{brief}

## Current Phase
{PHASE_LABELS.get(phase, phase)} ({phase})

## Team Members
{chr(10).join(f"- {label} ({role})" for role, label in PHASE_LABELS.items())}

## Your decision
Based on the current phase and any feedback, decide:
1. What task_instructions to give the active agent (be specific and detailed)
2. Optionally send a message to the human if clarification is needed

Be precise. The task_instructions you provide are the ONLY input the agent receives.
Include relevant context from previous artifacts in the instructions.
{"" if not feedback else f"IMPORTANT: The previous work was REJECTED with feedback: {feedback}. Include this in your instructions."}
"""
