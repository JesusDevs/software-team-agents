from state.schema import ProjectState, PHASE_ORDER, PHASE_LABELS


_PHASE_LABELS_ES = {
    "po":        "Product Owner",
    "ux":        "Diseñador UX",
    "architect": "Arquitecto de Software",
    "dev":       "Desarrollador Líder",
    "devops":    "Ingeniero DevOps",
}

_PHASE_ARTIFACTS_ES = {
    "po":        "01_PRD.md + 01_PRD_context.json",
    "ux":        "02_UX_SPEC.md + 02_UX_context.json",
    "architect": "03_SYSTEM_DESIGN.md + 03_ARCH_context.json",
    "dev":       "04_IMPLEMENTATION_SPEC.md + 04_DEV_context.json",
    "devops":    "05_DEVOPS_PLAN.md + 05_DEVOPS_context.json",
}


def get_system_prompt(state: ProjectState) -> str:
    phase    = state.get("current_phase", "po")
    feedback = state.get("hitl_feedback", "")
    artifacts = state.get("artifacts", {})
    brief    = state.get("project_brief", "")

    # Artefactos completados para memoria del supervisor
    completed = []
    for i, p in enumerate(PHASE_ORDER):
        if any(k.startswith(f"0{i+1}") for k in artifacts):
            completed.append(f"✅ {_PHASE_LABELS_ES.get(p, p)}: {_PHASE_ARTIFACTS_ES.get(p, '')}")

    completed_str = "\n".join(completed) if completed else "Ninguno aún."

    feedback_block = (
        f"\n\n## ⚠️ FEEDBACK DEL HUMANO (trabajo rechazado)\n{feedback}\nInstruye al agente a corregirlo."
        if feedback else ""
    )

    return f"""Eres el Supervisor de un equipo de desarrollo de software IA. Eres estratégico, claro y das instrucciones precisas.

## Brief del Proyecto
{brief}

## Fase Actual
{_PHASE_LABELS_ES.get(phase, phase)} ({phase})

## Artefactos Completados (memoria del equipo)
{completed_str}

## Tu equipo
{chr(10).join(f"- {label} ({role}): produce {_PHASE_ARTIFACTS_ES.get(role, '')}" for role, label in _PHASE_LABELS_ES.items())}

## Tu decisión
1. Escribe task_instructions DETALLADAS en español para el agente activo
2. Incluye contexto de artefactos anteriores relevantes
3. Especifica claramente el nombre del archivo a guardar
4. Si hay JSON de contexto disponible de fases anteriores, cítalo en las instrucciones
{feedback_block}

Sé específico y concreto. Las task_instructions son el ÚNICO input que recibe el agente."""
