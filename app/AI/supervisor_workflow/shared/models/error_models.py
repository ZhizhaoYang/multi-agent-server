from pydantic import BaseModel
from typing import Optional

from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_Dept


class ChatError(BaseModel):
    node_name: str
    from_department: Optional[NodeNames_Dept] = None
    error_message: str
    type: str
    timestamp: str