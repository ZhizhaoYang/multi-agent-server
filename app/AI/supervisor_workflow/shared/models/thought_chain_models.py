"""
Simple ThoughtChain Models

Basic models for showing AI thinking process to users
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import uuid4


class ThoughtType(Enum):
    """Simple thought types"""
    REASONING = "reasoning"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    WORKING = "working"
    CHECKING = "checking"
    RESULT = "result"


class ThoughtSegment(BaseModel):
    """A single thought segment"""
    segment_id: str = Field(default_factory=lambda: f"seg_{uuid4().hex[:8]}")
    content: str = Field(..., description="The thought content")
    marker: str = Field(..., description="Thought marker like 'THOUGHT:', 'WORKING:', etc.")
    thought_type: ThoughtType = Field(..., description="Type of thinking")
    is_complete: bool = Field(default=False, description="Whether this segment is finished")
    is_result: bool = Field(default=False, description="Whether this is the final RESULT")
    department: str = Field(..., description="Which department generated this thought")
    timestamp: datetime = Field(default_factory=datetime.now)


