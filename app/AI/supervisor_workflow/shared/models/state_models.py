from pydantic import BaseModel, Field
from typing import List, Set
from langchain_core.messages import AnyMessage
from langgraph.types import StreamWriter
from langgraph.graph.message import add_messages
from typing import Annotated, Optional
from datetime import datetime, timezone
import operator

from app.AI.supervisor_workflow.shared.utils.stateUtils import latest_value_reducer
from app.AI.supervisor_workflow.shared.models.Assessment import Task, CompletedTask, LLMAssessmentOutput
from app.AI.supervisor_workflow.shared.models.error_models import ChatError
from app.AI.supervisor_workflow.shared.models.enums import SupervisorStatus
from app.AI.supervisor_workflow.shared.utils.stateUtils import create_state_merger, upsert_by_task_id


# ThoughtChain models have been moved to thought_chain_models.py for better organization
from .thought_chain_models import ThoughtSegment

# =============================================================================
# CORE STATE MODELS
# =============================================================================

class AssessmentState(BaseModel):
    """State for assembly workflow and task management"""
    assessment_report: Optional[LLMAssessmentOutput] = Field(
        default=None,
        description="The LLM assessment result"
    )

    assessment_summary: Annotated[Optional[str], latest_value_reducer] = Field(
        default=None,
        description="Brief summary of the assessment"
    )


class SupervisorState(BaseModel):
    """State for supervisor workflow and task management"""
    supervisor_status: SupervisorStatus = Field(
        default=SupervisorStatus.IDLE,
        description="Current status of the supervisor workflow"
    )

    dispatched_tasks: Annotated[List[Task], upsert_by_task_id] = Field(
        default_factory=list,
        description="Tasks that have been dispatched to departments"
    )

    dispatched_task_ids: Annotated[Set[str], operator.or_] = Field(
        default_factory=set,
        description="Set of dispatched task IDs for quick lookup"
    )

    completed_tasks: Annotated[List[CompletedTask], upsert_by_task_id] = Field(
        default_factory=list,
        description="Tasks that have been completed by departments (with upsert behavior by task_id)"
    )

    completed_task_ids: Annotated[Set[str], operator.or_] = Field(
        default_factory=set,
        description="Set of completed task IDs for quick lookup"
    )


class WorkflowState(BaseModel):
    """State for workflow debugging and internal processing metadata"""
    thoughts: Annotated[str, latest_value_reducer] = Field(
        default="",
        description="Internal reasoning and thoughts during processing"
    )

    # processing_metadata: Dict[str, Any] = Field(
    #     default_factory=dict,
    #     description="Metadata for debugging and performance monitoring"
    #         )


class ChatState(BaseModel):
    """
    Unified chat state with top-level core fields for LangGraph Studio compatibility.
    Core fields are at the top level, organized fields are grouped.
    """

    user_query: Annotated[str, latest_value_reducer] = Field(default="", description="The user's input query")

    messages: Annotated[List[AnyMessage], add_messages] = Field(
        default_factory=list,
        description="Conversation messages flowing through the graph"
    )

    final_output: Annotated[str, latest_value_reducer] = Field(default="", description="Final response to the user")

    errors: Annotated[List[ChatError], operator.add] = Field(
        default_factory=list,
        description="Errors that occurred during processing"
    )

    stream_queue_id: Optional[str] = Field(
        default=None,
        description="ID of the stream queue for this chat session"
    )

    # Assessment-specific state
    assessment: AssessmentState = Field(default_factory=lambda: AssessmentState())

    # Supervisor-specific state - with custom reducer for concurrent updates
    supervisor: Annotated[SupervisorState, create_state_merger(
        SupervisorState)] = Field(default_factory=lambda: SupervisorState())

    # Workflow-specific state for debugging and internal processing
    workflow: WorkflowState = Field(default_factory=lambda: WorkflowState())

            # ThoughtChain state - streaming thoughts during processing
    thinking_enabled: bool = Field(default=True, description="Whether thinking mode is enabled")
    thought_segments: List[ThoughtSegment] = Field(default_factory=list, description="All thought segments generated")
    last_streamed_thought_id: Optional[str] = Field(default=None, description="ID of last streamed thought")
    streamed_thought_ids: Set[str] = Field(default_factory=set, description="Set of already streamed thought IDs")

    # Convenience methods
    def add_error(self, error: Exception, node_name: str):
        """Convenience method to add an error to the state"""
        self.errors.append(self.build_error(error, node_name))

    def build_error(self, error: Exception, node_name: str) -> ChatError:
        """Build a ChatError from an exception"""
        return ChatError(
            node_name=node_name,
            error_message=str(error),
            type=type(error).__name__,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def get_stream_publisher(self):
        """Get a stream publisher for this chat session"""
        from app.AI.supervisor_workflow.shared.models.stream_models import create_stream_publisher
        return create_stream_publisher(self.stream_queue_id)
