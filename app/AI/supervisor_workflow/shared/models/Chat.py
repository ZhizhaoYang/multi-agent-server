from pydantic import BaseModel, Field
from typing import List
from uuid import uuid4
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing import Annotated, Optional
from datetime import datetime, timezone
import operator

from app.AI.supervisor_workflow.shared.models.Assessment import Task
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_Dept
from app.AI.supervisor_workflow.shared.models.Assessment import LLMAssessmentOutput

class ChatError(BaseModel):
    node_name: str
    from_department: Optional[NodeNames_Dept] = None
    error: str
    type: str
    timestamp: str

class ChatState(BaseModel):
    """
    Chat model for the supervisor workflow.
    """

    # thread_id is the id of the thread that the chat is associated with.
    thread_id: str = Field(
        default_factory=lambda: f"th_{uuid4().hex[:10]}",
        frozen=True
    )

    user_query: str = Field(frozen=True)

    thoughts: str = Field(default="")

    messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list)

    assessment_report: Optional[LLMAssessmentOutput] = Field(default=None)
    assessment_summary: Optional[str] = Field(default="")
    dispatched_tasks: List[Task] = Field(default=[])
    completed_tasks: List[Task] = Field(default=[])

    final_output: str = Field(default="")

    errors: Annotated[List[ChatError], operator.add] = Field(default_factory=list)

    # add_error is a convenience method to add an error to this chat state.
    def add_error(self, error: Exception, node_name: str):
        self.errors.append(self.build_error(error, node_name))

    def build_error(self, error: Exception, node_name: str):
        return ChatError(
            node_name=node_name,
            error=str(error),
            type=type(error).__name__,
            timestamp=datetime.now(timezone.utc).isoformat()
        )



