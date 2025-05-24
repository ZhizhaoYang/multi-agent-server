import json
from pydantic import BaseModel
from enum import Enum


class EventType(Enum):
    DATA = "data"
    ERROR = "error"
    COMPLETE = "complete"


class SSEMessage:
    def __init__(self, data, event=None, id=None):
        self.data = data
        self.event = event
        self.id = id

    def __str__(self):
        lines = []
        if self.event:
            lines.append(f"event: {self.event}")
        if self.id:
            lines.append(f"id: {self.id}")
        lines.append(f"data: {json.dumps(self.data)}")
        return "\n".join(lines) + "\n\n"


class StreamChunk(BaseModel):
    event_type: EventType
    content: str
    # timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict = {}

    def model_dump_sse(self) -> str:
        """Formats for SSE protocol"""
        return f"event: {self.event_type}\ndata: {self.model_dump_json()}\n\n"
