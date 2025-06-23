from pydantic import BaseModel, Field
from uuid import uuid4
from typing import List
from langchain_core.messages import AnyMessage

class UserContext(BaseModel):
    """Simplified user context with essential fields only"""
    thread_id: str = Field(
        default_factory=lambda: f"th_{uuid4().hex[:10]}",
        frozen=True,
        description="Unique identifier for this conversation thread"
    )

    history_messages: List[AnyMessage] = Field(default=[], description="History messages")

    # Core user identity
    user_id: str = Field(..., description="Unique user identifier")
    user_role: str = Field(default="user", description="User role: admin, user, guest, premium")

    # Essential preferences
    preferred_language: str = Field(default="en", description="Language preference: en, zh, es, fr")