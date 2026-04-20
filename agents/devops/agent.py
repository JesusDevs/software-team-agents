from datetime import datetime, timezone
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from llm.models import get_model_for_agent
from tools.shared.artifacts import save_artifact, read_artifact, list_artifacts, load_artifacts_from_fs
from tools.shared.search import web_search
from tools.shared.knowledge import make_search_knowledge_tool
from tools.hitl.question import ask_question
from agents.devops.prompt import get_system_prompt
from state.schema import ProjectState

ROLE = "devops"
TOOLS = [save_artifact, read_artifact, list_artifacts, web_search,
         make_search_knowledge_tool(ROLE), ask_question]
TOOL_MAP = {t.name: t for t in TOOLS}


def devops_agent_node(state: ProjectState, config: RunnableConfig) -> dict:
    run_id = state.get("run_id", "default")
    llm = get_model_for_agent(ROLE).bind_tools(TOOLS)
    task = state.get("task_instructions") or "Create the DevOps and infrastructure plan."

    messages = [
        SystemMessage(content=get_system_prompt(state)),
        HumanMessage(content=f"Task: {task}\n\nrun_id={run_id}"),
    ]

    new_messages = []
    input_tokens = output_tokens = 0

    for _ in range(12):
        response = llm.invoke(messages)
        messages.append(response)
        new_messages.append(response)

        if hasattr(response, "usage_metadata") and response.usage_metadata:
            input_tokens += response.usage_metadata.get("input_tokens", 0)
            output_tokens += response.usage_metadata.get("output_tokens", 0)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            fn = TOOL_MAP.get(tc["name"])
            args = dict(tc["args"])
            if tc["name"] in ("save_artifact", "read_artifact", "list_artifacts"):
                args.setdefault("run_id", run_id)
            if tc["name"] == "save_artifact":
                args.setdefault("agent", ROLE)
            try:
                result = fn.invoke(args)
                tool_msg = ToolMessage(content=str(result), tool_call_id=tc["id"], name=tc["name"])
            except Exception as e:
                tool_msg = ToolMessage(content=f"Error: {e}", tool_call_id=tc["id"], name=tc["name"])
            messages.append(tool_msg)
            new_messages.append(tool_msg)

    artifacts = load_artifacts_from_fs(run_id)
    token_usage = dict(state.get("token_usage", {}))
    prev = token_usage.get(ROLE, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
    token_usage[ROLE] = {
        "input_tokens": prev["input_tokens"] + input_tokens,
        "output_tokens": prev["output_tokens"] + output_tokens,
        "total_tokens": prev["total_tokens"] + input_tokens + output_tokens,
    }

    handoff_log = list(state.get("handoff_log", []))
    handoff_log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from_agent": ROLE, "to_agent": "hitl_gate",
        "message": f"Completed {ROLE.upper()} phase",
        "task_instructions": task,
    })

    return {
        "messages": new_messages,
        "current_phase": ROLE,
        "artifacts": artifacts,
        "token_usage": token_usage,
        "handoff_log": handoff_log,
    }
