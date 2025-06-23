from langgraph.graph import StateGraph, START, END
from typing import Dict
from langchain_core.runnables.base import Runnable
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import os
# import sqlite3
import aiosqlite

from app.AI.supervisor_workflow.shared.models import ChatState
from app.AI.supervisor_workflow.head_quarter.nodes import assessment_node, supervisor_node, aggregator_node, final_response_node, initializer_node
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_HQ
from app.AI.supervisor_workflow.head_quarter.dept_registry_center import department_registry

ENV = os.environ.get("ENV", "dev")
CHECKPOINTER_PATH = os.environ.get("CHECKPOINTER_PATH", "db/checkpoints/checkpoints.sqlite")

AVAILABLE_DEPT_MAP: Dict[str, Runnable] = department_registry.get_available_departments_func_map()

# Initialize checkpointer for conversation history
checkpointer = None
if ENV == "dev":
    conn = aiosqlite.connect(CHECKPOINTER_PATH, check_same_thread=False)
    checkpointer = AsyncSqliteSaver(conn)


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

# Add department nodes
for name in department_registry.get_available_department_names():
    builder.add_node(name, AVAILABLE_DEPT_MAP[name])
    builder.add_edge(name, NodeNames_HQ.SUPERVISOR.value)

# Define main workflow edges
builder.add_edge(START, NodeNames_HQ.INITIALIZER.value)
builder.add_edge(NodeNames_HQ.INITIALIZER.value, NodeNames_HQ.ASSESSMENT.value)
builder.add_edge(NodeNames_HQ.ASSESSMENT.value, NodeNames_HQ.SUPERVISOR.value)
builder.add_edge(NodeNames_HQ.AGGREGATOR.value, NodeNames_HQ.FINAL_RESPONSE.value)
builder.add_edge(NodeNames_HQ.FINAL_RESPONSE.value, END)

main_graph = builder.compile(checkpointer=checkpointer)








