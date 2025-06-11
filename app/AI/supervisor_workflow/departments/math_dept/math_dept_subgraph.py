from langgraph.types import Command
from langgraph.graph import StateGraph, START, END

from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput

def math_expert_node(dept_input: DeptInput) -> Command:
    print(f"*** Math department subgraph received task: {dept_input.task} ***")

    return Command(
        update={},
        goto=Command.PARENT
    )

_builder = StateGraph(DeptInput)

_builder.add_node(
    "math_expert",
    math_expert_node
)

_builder.add_edge(START, "math_expert")
_builder.add_edge("math_expert", END)

math_dept_subgraph = _builder.compile()

