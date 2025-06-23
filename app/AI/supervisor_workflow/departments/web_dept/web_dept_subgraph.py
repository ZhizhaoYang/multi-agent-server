from langgraph.graph import StateGraph, START, END

from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput
from app.AI.supervisor_workflow.departments.web_dept.nodes.web_searcher_node import web_searcher_node

_builder = StateGraph(DeptInput)

_builder.add_node(
    "web_searcher",
    web_searcher_node
)

_builder.add_edge(START, "web_searcher")
_builder.add_edge("web_searcher", END)

# No checkpointer needed - conversation history comes from main graph via DeptInput.messages
web_dept_subgraph = _builder.compile()

