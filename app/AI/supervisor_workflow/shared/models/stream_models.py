from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal
from datetime import datetime
from app.utils.stream_queue_manager import StreamQueueManager
from app.utils.logger import logger


class StreamEvent(BaseModel):
    """
    Event model for streaming thoughts and updates between subgraphs and main graph.
    """
    event_type: Literal["thought", "thought_complete", "progress", "error", "result"] = Field(
        ..., description="Type of the stream event"
    )
    source: str = Field(..., description="Source department or node name")
    content: str = Field(..., description="The actual content/message")
    segment_id: int = Field(..., description="Sequential ID for ordering events")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")

    def to_dict(self) -> dict:
        """Convert to dictionary for queue transmission"""
        return {
            "event_type": self.event_type,
            "source": self.source,
            "content": self.content,
            "segment_id": self.segment_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'StreamEvent':
        """Create from dictionary received from queue"""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class StreamPublisher:
    """
    Publisher interface for departments to send stream events.
    """

    def __init__(self, queue_id: Optional[str]):
        self.queue_id = queue_id
        self.queue_manager = StreamQueueManager.get_instance()

    async def publish(self, event: StreamEvent):
        """
        Publish a stream event to the queue.

        Args:
            event: The stream event to publish
        """
        if not self.queue_id:
            logger.warning("No queue_id provided, cannot publish stream event")
            return

        try:
            await self.queue_manager.put_event(self.queue_id, event.to_dict())
            logger.debug(f"Published event: {event.event_type} from {event.source}")
        except Exception as e:
            logger.error(f"Failed to publish stream event: {e}")

    async def publish_thought(self, content: str, source: str, segment_id: int, metadata: Optional[Dict[str, Any]] = None):
        """
        Convenience method to publish a thought event.

        Args:
            content: The thought content
            source: Source department name
            segment_id: Sequential segment ID
            metadata: Optional metadata
        """
        event = StreamEvent(
            event_type="thought",
            source=source,
            content=content,
            segment_id=segment_id,
            metadata=metadata or {}
        )
        await self.publish(event)

    async def publish_thought_complete(self, source: str, segment_id: int, total_length: Optional[int] = None):
        """
        Convenience method to publish thought completion.

        Args:
            source: Source department name
            segment_id: Final segment ID
            total_length: Total number of characters/segments
        """
        metadata = {}
        if total_length is not None:
            metadata["total_length"] = total_length

        event = StreamEvent(
            event_type="thought_complete",
            source=source,
            content="",
            segment_id=segment_id,
            metadata=metadata
        )
        await self.publish(event)

    async def publish_progress(self, content: str, source: str, progress_percent: float):
        """
        Convenience method to publish progress updates.

        Args:
            content: Progress description
            source: Source department name
            progress_percent: Progress percentage (0-100)
        """
        event = StreamEvent(
            event_type="progress",
            source=source,
            content=content,
            segment_id=0,  # Progress events don't need segment ordering
            metadata={"progress_percent": progress_percent}
        )
        await self.publish(event)


class StreamConsumer:
    """
    Consumer interface for consuming stream events from queues.
    """

    def __init__(self, queue_id: str):
        self.queue_id = queue_id
        self.queue_manager = StreamQueueManager.get_instance()

    async def consume_event(self, timeout: float = 1.0) -> Optional[StreamEvent]:
        """
        Consume a single stream event from the queue.

        Args:
            timeout: Timeout in seconds

        Returns:
            StreamEvent or None if timeout/error
        """
        try:
            event_dict = await self.queue_manager.get_event(self.queue_id, timeout)
            if event_dict:
                return StreamEvent.from_dict(event_dict)
            return None
        except Exception as e:
            logger.error(f"Failed to consume stream event: {e}")
            return None

    async def consume_events(self, timeout_per_event: float = 1.0):
        """
        Async generator to continuously consume events from the queue.

        Args:
            timeout_per_event: Timeout per event in seconds

        Yields:
            StreamEvent instances
        """
        while True:
            event = await self.consume_event(timeout_per_event)
            if event:
                yield event
            else:
                # No event received within timeout, continue listening
                continue


def create_stream_publisher(queue_id: Optional[str]) -> StreamPublisher:
    """Factory function to create a stream publisher"""
    return StreamPublisher(queue_id)


def create_stream_consumer(queue_id: str) -> StreamConsumer:
    """Factory function to create a stream consumer"""
    return StreamConsumer(queue_id)