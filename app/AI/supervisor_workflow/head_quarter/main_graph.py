from langgraph.graph import StateGraph, START, END
from typing import Dict
from langchain_core.runnables.base import Runnable

from app.AI.supervisor_workflow.shared.models import ChatState
from app.AI.supervisor_workflow.head_quarter.nodes import (
    assessment_node,
    supervisor_node,
    aggregator_node,
    final_response_node,
    initializer_node
)
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_HQ
from app.AI.supervisor_workflow.head_quarter.dept_registry_center import department_registry
from app.AI.supervisor_workflow.shared.utils.checkpointer_manager import get_best_checkpointer

# Get available departments
AVAILABLE_DEPT_MAP: Dict[str, Runnable] = department_registry.get_available_departments_func_map()

def _build_workflow_graph() -> StateGraph:
    """Build the complete workflow graph with all nodes and edges"""
    builder = StateGraph(ChatState)

    # Add main workflow nodes
    builder.add_node(NodeNames_HQ.INITIALIZER.value, initializer_node)
    builder.add_node(NodeNames_HQ.ASSESSMENT.value, assessment_node)
    builder.add_node(
        NodeNames_HQ.SUPERVISOR.value,
        supervisor_node,
        destinations=(*department_registry.get_available_department_names(), NodeNames_HQ.AGGREGATOR.value)
    )
    builder.add_node(NodeNames_HQ.AGGREGATOR.value, aggregator_node)
    builder.add_node(NodeNames_HQ.FINAL_RESPONSE.value, final_response_node)

    # Add department nodes and their edges
    for name in department_registry.get_available_department_names():
        builder.add_node(name, AVAILABLE_DEPT_MAP[name])
        builder.add_edge(name, NodeNames_HQ.SUPERVISOR.value)

    # Define main workflow edges
    builder.add_edge(START, NodeNames_HQ.INITIALIZER.value)
    builder.add_edge(NodeNames_HQ.INITIALIZER.value, NodeNames_HQ.ASSESSMENT.value)
    builder.add_edge(NodeNames_HQ.ASSESSMENT.value, NodeNames_HQ.SUPERVISOR.value)
    builder.add_edge(NodeNames_HQ.AGGREGATOR.value, NodeNames_HQ.FINAL_RESPONSE.value)
    builder.add_edge(NodeNames_HQ.FINAL_RESPONSE.value, END)

    return builder

# Global variables for graph management
_main_graph_with_checkpointer = None
_graph_initialized = False

# Create the graph builder and basic graph
builder = _build_workflow_graph()
main_graph = builder.compile()

async def get_main_graph_with_checkpointer():
    """Get the main graph with the best available checkpointer"""
    global _main_graph_with_checkpointer, _graph_initialized

    if not _graph_initialized:
        # Try to get a persistent checkpointer
        checkpointer = await get_best_checkpointer()

        if checkpointer:
            _main_graph_with_checkpointer = builder.compile(checkpointer=checkpointer)
        else:
            print("📝 No persistent checkpointer available, using in-memory checkpointing")
            _main_graph_with_checkpointer = builder.compile()

        _graph_initialized = True

    return _main_graph_with_checkpointer

def get_main_graph():
    """Synchronous function to get the main graph (returns basic graph without checkpointer)"""
    return main_graph







