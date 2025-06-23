from langgraph.graph import StateGraph, START, END

from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput
from app.AI.supervisor_workflow.departments.general_knowledge_dept.nodes.general_knowledege_node import general_knowledge_node

_builder = StateGraph(DeptInput)

_builder.add_node(
    "general_knowledge",
    general_knowledge_node
)

_builder.add_edge(START, "general_knowledge")
_builder.add_edge("general_knowledge", END)

# No checkpointer needed - conversation history comes from main graph via DeptInput.messages
general_knowledge_subgraph = _builder.compile()
