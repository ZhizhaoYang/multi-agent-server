from langgraph.graph import StateGraph, START, END
from typing import Dict
from langchain_core.runnables.base import Runnable
from app.AI.supervisor_workflow.shared.models import ChatState
from app.AI.supervisor_workflow.head_quarter.nodes import assessment_node, supervisor_node
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_HQ
from .dept_registry_center import department_registry

AVAILABLE_DEPT_MAP: Dict[str, Runnable] = department_registry.get_available_departments_func_map()

builder = StateGraph(ChatState)


builder.add_node(NodeNames_HQ.ASSESSMENT.value, assessment_node)
builder.add_node(
    NodeNames_HQ.SUPERVISOR.value,
    supervisor_node,
    destinations=tuple(department_registry.get_available_department_names())
)

for name in department_registry.get_available_department_names():
    builder.add_node(name, AVAILABLE_DEPT_MAP[name])


builder.add_edge(START, NodeNames_HQ.ASSESSMENT.value)
builder.add_edge(NodeNames_HQ.ASSESSMENT.value, NodeNames_HQ.SUPERVISOR.value)

for department in AVAILABLE_DEPT_MAP.keys():
    builder.add_edge(NodeNames_HQ.SUPERVISOR.value, department)

builder.add_edge(NodeNames_HQ.SUPERVISOR.value, END)


main_graph = builder.compile()
