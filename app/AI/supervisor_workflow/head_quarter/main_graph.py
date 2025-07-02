from langgraph.graph import StateGraph, START, END
from typing import Dict
from langchain_core.runnables.base import Runnable
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import os
import asyncpg
import asyncio

from app.AI.supervisor_workflow.shared.models import ChatState
from app.AI.supervisor_workflow.head_quarter.nodes import assessment_node, supervisor_node, aggregator_node, final_response_node, initializer_node
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_HQ
from app.AI.supervisor_workflow.head_quarter.dept_registry_center import department_registry

ENV = os.environ.get("ENV", "dev")

# Supabase PostgreSQL connection configuration
DATABASE_URL = os.environ.get("SUPABASE_DB_URL")

AVAILABLE_DEPT_MAP: Dict[str, Runnable] = department_registry.get_available_departments_func_map()

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

# Global variable to store the initialized graph
_main_graph_with_checkpointer = None
_graph_initialized = False

# Create a basic graph without checkpointer for immediate use
main_graph = builder.compile()

async def get_main_graph_with_checkpointer():
    """Get the main graph with PostgreSQL checkpointer, initializing if needed"""
    global _main_graph_with_checkpointer, _graph_initialized

    if not _graph_initialized:
        if ENV == "production" and DATABASE_URL:
            try:
                # Create PostgreSQL checkpointer
                checkpointer_cm = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
                checkpointer = await checkpointer_cm.__aenter__()

                # Setup database tables for checkpointing
                await checkpointer.setup()
                print(f"✅ PostgreSQL checkpointer initialized successfully")

                _main_graph_with_checkpointer = builder.compile(checkpointer=checkpointer)
            except Exception as e:
                print(f"⚠️ Failed to initialize PostgreSQL checkpointer: {e}")
                print("📝 Falling back to in-memory checkpointing")
                _main_graph_with_checkpointer = builder.compile()
        else:
            print("📝 PostgreSQL credentials not provided, using in-memory checkpointing")
            _main_graph_with_checkpointer = builder.compile()

        _graph_initialized = True

    return _main_graph_with_checkpointer

def get_main_graph():
    """Synchronous function to get the main graph (returns basic graph without checkpointer)"""
    return main_graph







