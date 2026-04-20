"""CLI entry point — runs the pipeline headlessly (no UI)."""
import argparse
import uuid
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from graph.pipeline import get_pipeline
from config.settings import settings


def run(brief: str, run_id: str, auto_approve: bool = False):
    if not settings.has_openai_key():
        print("ERROR: OPENAI_API_KEY not set in .env")
        return

    pipeline = get_pipeline()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n{'='*60}")
    print(f"  Software Team Agents — CLI Run")
    print(f"  run_id:    {run_id}")
    print(f"  thread_id: {thread_id}")
    print(f"{'='*60}\n")

    initial_state = {
        "messages": [HumanMessage(content=brief)],
        "project_brief": brief,
        "run_id": run_id,
        "current_phase": "po",
        "next_agent": "po",
        "task_instructions": "",
        "hitl_feedback": "",
        "artifacts": {},
        "token_usage": {},
        "handoff_log": [],
        "error": "",
    }

    result = pipeline.invoke(initial_state, config=config)

    while True:
        interrupts = result.get("__interrupt__", [])
        if not interrupts:
            break

        iv = interrupts[0]
        payload = iv.get("value", iv) if isinstance(iv, dict) else getattr(iv, "value", iv)
        phase = payload.get("phase", "?")
        art_name = payload.get("artifact_name", "?")

        print(f"\n[HITL] Review required: {art_name} ({phase.upper()} agent)")
        print(f"{'─'*60}")
        print(payload.get("content", "")[:600])
        print(f"{'─'*60}")

        if auto_approve:
            print("[AUTO] Approving…")
            approved, feedback = True, ""
        else:
            ans = input("\nApprove? (y/n): ").strip().lower()
            approved = ans == "y"
            feedback = ""
            if not approved:
                feedback = input("Feedback: ").strip()

        result = pipeline.invoke(
            Command(resume={"approved": approved, "feedback": feedback}),
            config=config,
        )

    print("\n✅ Pipeline complete!")
    phase = result.get("current_phase", "")
    print(f"   Final phase: {phase}")
    print(f"   Artifacts: {list(result.get('artifacts', {}).keys())}")

    usage = result.get("token_usage", {})
    total = sum(v.get("total_tokens", 0) for v in usage.values())
    print(f"   Total tokens: {total:,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Software Team Agents CLI")
    parser.add_argument("--brief",  required=True, help="Project brief")
    parser.add_argument("--run-id", default="run_001", help="Run ID for artifact storage")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve all HITL gates")
    args = parser.parse_args()

    run(brief=args.brief, run_id=args.run_id, auto_approve=args.auto_approve)
