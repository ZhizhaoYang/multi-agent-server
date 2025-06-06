from langgraph.types import Command
from langgraph.graph import StateGraph, START, END


from app.AI.supervisor_workflow.shared.models.Assessment import Task

def math_expert_node(task: Task) -> Command:
    print(f"*** Math department subgraph received task: {task} ***")

    return Command(
        update={},
        goto=Command.PARENT
    )

_builder = StateGraph(Task)

_builder.add_node(
    "math_expert",
    math_expert_node
)

_builder.add_edge(START, "math_expert")
_builder.add_edge("math_expert", END)

math_dept_subgraph = _builder.compile()

