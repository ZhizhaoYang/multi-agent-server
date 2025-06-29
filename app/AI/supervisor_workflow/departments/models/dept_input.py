from pydantic import BaseModel
from typing import List, Optional
from langchain_core.messages import AnyMessage

from app.AI.supervisor_workflow.shared.models import Task
from app.AI.supervisor_workflow.shared.models.Chat import SupervisorState

class DeptInput(BaseModel):
    """
    Department input model with queue-based streaming support.
    Uses stream_queue_id instead of direct StreamWriter for serialization safety.
    """

    task: Task
    supervisor: SupervisorState
    # Conversation context for history access
    messages: List[AnyMessage] = []
    thread_id: str = ""
    user_query: str = ""
    stream_queue_id: Optional[str] = None

    def get_stream_publisher(self):
        """Get a stream publisher for this department"""
        from app.AI.supervisor_workflow.shared.models.stream_models import create_stream_publisher
        return create_stream_publisher(self.stream_queue_id)