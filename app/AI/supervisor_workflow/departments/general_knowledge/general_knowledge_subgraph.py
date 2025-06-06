from langgraph.types import Command
from langgraph.graph import StateGraph, START, END

from app.AI.supervisor_workflow.shared.models.Assessment import Task

def general_knowledge_node(task: Task) -> Command:
    print(f"*** General knowledge department received task: {task} ***")

    return Command(
        update={},
        goto=Command.PARENT
    )


_builder = StateGraph(Task)

_builder.add_node(
    "general_knowledge",
    general_knowledge_node
)

_builder.add_edge(START, "general_knowledge")
_builder.add_edge("general_knowledge", END)

general_knowledge_subgraph = _builder.compile()
