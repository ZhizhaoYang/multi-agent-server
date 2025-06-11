from pydantic import BaseModel

from app.AI.supervisor_workflow.shared.models import Task
from app.AI.supervisor_workflow.shared.models.Chat import SupervisorState

class DeptInput(BaseModel):
    task: Task
    supervisor: SupervisorState