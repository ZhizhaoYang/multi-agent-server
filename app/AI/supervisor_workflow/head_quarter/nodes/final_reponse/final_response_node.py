from langgraph.graph import END
from langgraph.types import Command


from app.AI.supervisor_workflow.shared.models import ChatState

def final_response_node(state: ChatState) -> Command:
    return Command(
        goto=END
    )