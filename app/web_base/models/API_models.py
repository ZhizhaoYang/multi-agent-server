from pydantic import BaseModel, Field
from typing import Optional, Literal, Annotated, List
from uuid import uuid4
import operator

from app.AI.workflows.models.chat_state import ChatWorkflowState
from app.AI.workflows.models.chat_state import ChatGraphContext
from app.AI.workflows.models.chat_state import ChatError



# API Request
class APIRequest(BaseModel):
    user_query: str = Field(..., min_length=1, max_length=2000,
                            description="User's input message")

    # conversation_id: Optional[str] = Field(
    #     None,
    #     pattern=r"^conv_[a-zA-Z0-9]{20}$",
    #     description="Existing conversation ID"
    # )

    stream: bool = True  # Enable SSE

    mode: Literal["fast", "precise", "creative"] = Field(
        "precise",
        description="Tradeoff between speed and accuracy"
    )

    thread_id: Optional[str] = Field(
        default_factory=lambda: f"th_{uuid4().hex[:10]}",
        frozen=True,
        description="Thread ID"
    )

    user_id: Optional[str] = None

class APIResponse(BaseModel):
    final_output: str
    thread_id: str
    conversation_id: str
    errors: Annotated[List[ChatError], operator.add]

    @classmethod
    def from_workflow_state(cls, state: ChatWorkflowState, request: APIRequest, context: ChatGraphContext) -> "APIResponse":
        """Construct from finalized workflow state"""
        return cls(
            final_output=state.current_output,
            thread_id=request.thread_id or context.thread_id,
            conversation_id=context.conversation_id,
            errors=state.errors
        )
