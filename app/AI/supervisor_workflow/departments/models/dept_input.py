from pydantic import BaseModel
from typing import List
from langchain_core.messages import AnyMessage

from app.AI.supervisor_workflow.shared.models import Task
from app.AI.supervisor_workflow.shared.models.Chat import SupervisorState

class DeptInput(BaseModel):
    task: Task
    supervisor: SupervisorState
    # Conversation context for history access
    messages: List[AnyMessage] = []
    thread_id: str = ""
    user_query: str = ""