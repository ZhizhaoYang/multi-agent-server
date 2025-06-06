from pydantic import BaseModel, Field
from uuid import uuid4

class APIRequest(BaseModel):
    user_query: str = Field(..., min_length=1, max_length=2000, description="User's input message")

    thread_id: str = Field(
        default_factory=lambda: f"th_{uuid4().hex[:10]}",
        frozen=True,
        description="Thread ID for query"
    )


# class APIResponse(BaseModel):
#     final_output: str
#     thread_id: str
#     errors: Annotated[List[ChatError], operator.add]

#     @classmethod
#     def from_workflow_state(cls, state: ChatWorkflowState, request: APIRequest) -> "APIResponse":
#         """Construct from finalized workflow state"""
#         return cls(
#             final_output=state.final_output,
#             thread_id=request.thread_id,
#             errors=state.errors
#         )
