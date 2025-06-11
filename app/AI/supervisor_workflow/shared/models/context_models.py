from pydantic import BaseModel, Field
from typing import List


class UserContext(BaseModel):
    """Simplified user context with essential fields only"""

    # Core user identity
    user_id: str = Field(..., description="Unique user identifier")
    user_role: str = Field(default="user", description="User role: admin, user, guest, premium")

    # Essential preferences
    preferred_language: str = Field(default="en", description="Language preference: en, zh, es, fr")
    response_style: str = Field(default="balanced", description="Response style: concise, balanced, detailed, technical")

    # Multi-agent essentials
    max_tasks_per_assessment: int = Field(default=5, description="Maximum tasks per assessment")

    # Convenience methods
    def is_admin(self) -> bool:
        return self.user_role == "admin"

    def is_premium(self) -> bool:
        return self.user_role in ["premium", "enterprise", "admin"]

    def get_max_tasks(self) -> int:
        # Premium users get more tasks
        if self.is_premium():
            return min(self.max_tasks_per_assessment + 3, 10)
        return self.max_tasks_per_assessment