from typing import List, Optional, Annotated, Literal, Set
import operator
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from enum import Enum
from uuid import uuid4

class ChatError(BaseModel):
    node: str
    error: str
    type: str
    timestamp: str


class ChatNodeType(Enum):
    SUPERVISOR = "supervisor"
    WORKER = "worker"


class ChatNode(BaseModel):
    name: str
    description: Optional[str] = None
    type: Literal[ChatNodeType.SUPERVISOR, ChatNodeType.WORKER]


class ChatWorkflowState(BaseModel):
    # user_query: str = Field(frozen=True)
    messages: Annotated[list[AnyMessage],
                        add_messages] = Field(default_factory=list)

    next_steps: Annotated[List[ChatNode], operator.add] = Field(
        default_factory=list)

    current_output: str
    errors: Annotated[List[ChatError], operator.add] = Field(
        default_factory=list)

    step_count: int = 0  # Add a step counter for supervisor pattern safety
    visited_workers: Set[str] = Field(default_factory=set)
    supervisor_completed: bool = False

    def add_error(self, error: Exception, node: str):
        """Standard error logging"""
        self.errors.append(ChatError(
            node=node,
            error=str(error),
            type=type(error).__name__,
            timestamp=datetime.now(timezone.utc).isoformat()
        ))


class ChatGraphContext(BaseModel):
    user_query: str = Field(frozen=True)

    thread_id: str = Field(
        default_factory=lambda: f"th_{uuid4().hex[:10]}",
        frozen=True
    )

    conversation_id: str = Field(
        default_factory=lambda: f"conv_{uuid4().hex[:20]}",
        frozen=True
    )

    # @classmethod
    # def from_request(cls, request: APIRequest) -> "ChatGraphContext":
    #     """Transform API input into execution context"""
    #     return cls(
    #         user_query=request.user_query,
    #         thread_id=request.thread_id,
    #         # conversation_id=request.conversation_id or f"conv_{uuid4().hex[:20]}"
    #     )

