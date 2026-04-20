from langgraph.graph import StateGraph, START, END

from state.schema import ProjectState
from agents.po.agent import po_agent_node
from agents.ux.agent import ux_agent_node
from agents.architect.agent import architect_agent_node
from agents.dev.agent import dev_agent_node
from agents.devops.agent import devops_agent_node
from agents.supervisor.agent import supervisor_node, route_from_supervisor
from tools.hitl.approval import hitl_gate
from graph.checkpointer import get_checkpointer

_compiled_graph = None


def create_pipeline():
    builder = StateGraph(ProjectState)

    # Nodes
    builder.add_node("supervisor",      supervisor_node)
    builder.add_node("po_agent",        po_agent_node)
    builder.add_node("ux_agent",        ux_agent_node)
    builder.add_node("architect_agent", architect_agent_node)
    builder.add_node("dev_agent",       dev_agent_node)
    builder.add_node("devops_agent",    devops_agent_node)
    builder.add_node("hitl_gate",       hitl_gate)

    # Entry
    builder.add_edge(START, "supervisor")

    # Supervisor → agent (conditional)
    builder.add_conditional_edges("supervisor", route_from_supervisor, {
        "po_agent":        "po_agent",
        "ux_agent":        "ux_agent",
        "architect_agent": "architect_agent",
        "dev_agent":       "dev_agent",
        "devops_agent":    "devops_agent",
        "__end__":         END,
    })

    # Each agent → HITL gate
    for agent_node in ("po_agent", "ux_agent", "architect_agent", "dev_agent", "devops_agent"):
        builder.add_edge(agent_node, "hitl_gate")

    # hitl_gate routes via Command(goto=...) — no static edge needed

    return builder.compile(checkpointer=get_checkpointer())


def get_pipeline():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_pipeline()
    return _compiled_graph


def reset_pipeline():
    global _compiled_graph
    _compiled_graph = None
