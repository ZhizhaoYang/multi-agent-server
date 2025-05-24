from langgraph.graph import StateGraph, START, END
from enum import Enum

from app.AI.workflows.models.chat_state import ChatWorkflowState
from app.AI.workflows.nodes.general_response import general_response_node
from app.AI.workflows.nodes.supervisor import supervisor_node
from langgraph.checkpoint.memory import InMemorySaver

class Nodes(Enum):
    """langgraph Nodes"""
    GENERAL_RESPONSE = "generalResponse"
    SUPERVISOR = "supervisor"

# Configure InMemorySaver for thread-level persistence
# This saves conversation state in memory between interactions
# Note: For production, consider using PostgresSaver or SQLiteSaver instead
checkpointer = InMemorySaver()

builder = StateGraph(ChatWorkflowState)

builder.add_node(Nodes.GENERAL_RESPONSE.value, general_response_node)

builder.add_edge(START, Nodes.GENERAL_RESPONSE.value)
builder.add_edge(Nodes.GENERAL_RESPONSE.value, END)

graph = builder.compile(checkpointer=checkpointer)