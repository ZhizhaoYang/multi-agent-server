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


# Simple thought markers
THOUGHT_MARKERS = {
    "THOUGHT:": ThoughtType.REASONING,
    "ANALYSIS:": ThoughtType.ANALYSIS,
    "APPROACH:": ThoughtType.PLANNING,
    "WORKING:": ThoughtType.WORKING,
    "CHECKING:": ThoughtType.CHECKING,
    "RESULT:": ThoughtType.RESULT
}


def create_thinking_prompt(task_description: str, context: str = "") -> str:
    """Simple thinking prompt that works reliably"""

    prompt = f"""You are solving: {task_description}

Think step by step and show your reasoning. Use these markers:

THOUGHT: What I need to understand about this problem
ANALYSIS: Breaking down the key parts
APPROACH: My plan to solve this
WORKING: Step-by-step calculations or work
CHECKING: Verifying my solution
RESULT: Final answer only

Each marker should start on a new line. Write actual thoughts, not placeholders.

{context}

Start thinking:

THOUGHT:"""

    return prompt

