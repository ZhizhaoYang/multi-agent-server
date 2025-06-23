from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AnyMessage, HumanMessage
from typing import List, Dict, Any, Optional

from app.AI.supervisor_workflow.shared.models.Chat import ChatState, SupervisorStatus, AssessmentState
from app.AI.supervisor_workflow.shared.models.state_models import SupervisorState, WorkflowState
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_HQ


def create_new_turn_state(user_query: str, messages: List[AnyMessage] = []) -> Optional[ChatState]:
    """
    Create state for new conversation turn that preserves history.

    Key principles:
    1. Only add the NEW user message (add_messages reducer will merge with history)
    2. Only reset processing-specific state that should be cleared each turn
    3. Let checkpointer handle loading existing conversation history
    4. Preserve all conversation context across turns

    Args:
        user_query: The current user's query

    Returns:
        Dict containing minimal state updates for new conversation turn
    """
    return ChatState(
        # Initial current turn data
        user_query=user_query,
        messages=[HumanMessage(content=user_query)],
        final_output="",
        errors=[],
        assessment=AssessmentState(
            assessment_report=None,
            assessment_summary=None
        ),

        supervisor=SupervisorState(
            supervisor_status=SupervisorStatus.IDLE,
            dispatched_tasks=[],
            dispatched_task_ids=set(),
            completed_tasks=[],
            completed_task_ids=set()
        ),

        workflow=WorkflowState(
            thoughts=""
        )
    )


async def initializer_node(state: ChatState) -> Command:
    init_state = create_new_turn_state(state.user_query)

    return Command(
        update=init_state,
        goto=NodeNames_HQ.ASSESSMENT.value
    )

