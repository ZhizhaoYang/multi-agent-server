from langgraph.graph import StateGraph, START, END

from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput
from app.AI.supervisor_workflow.departments.math_dept.nodes.math_dept_node import math_dept_node

_builder = StateGraph(DeptInput)

_builder.add_node(
    "math_dept",
    math_dept_node
)

_builder.add_edge(START, "math_dept")
_builder.add_edge("math_dept", END)

# No checkpointer needed - conversation history comes from main graph via DeptInput.messages
math_dept_subgraph = _builder.compile()

