from langgraph.types import Command
from langgraph.graph import StateGraph, START, END


from app.AI.supervisor_workflow.shared.models.Assessment import Task

def web_searcher_node(task: Task) -> Command:
    print(f"*** Web department subgraph received task: {task} ***")

    return Command(
        update={},
        goto=Command.PARENT
    )

_builder = StateGraph(Task)

_builder.add_node(
    "web_searcher",
    web_searcher_node
)

_builder.add_edge(START, "web_searcher")
_builder.add_edge("web_searcher", END)

web_dept_subgraph = _builder.compile()

