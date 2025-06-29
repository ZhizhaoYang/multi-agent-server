import asyncio
from typing import Dict, Optional
from uuid import uuid4
import weakref
from app.utils.logger import logger


class StreamQueueManager:
    """
    Singleton manager for handling stream queues across the application.
    Uses weak references to allow automatic cleanup of unused queues.
    """
    _instance = None

    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._queue_refs: Dict[str, weakref.ReferenceType] = {}

    @classmethod
    def get_instance(cls) -> 'StreamQueueManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_queue(self, thread_id: str) -> str:
        """
        Create a new queue for a thread and return its ID.

        Args:
            thread_id: The thread identifier

        Returns:
            queue_id: Unique identifier for the created queue
        """
        queue_id = f"queue_{thread_id}_{uuid4().hex[:8]}"
        queue = asyncio.Queue()

        self._queues[queue_id] = queue

        # Create weak reference for automatic cleanup
        def cleanup(ref):
            self._cleanup_queue(queue_id)

        self._queue_refs[queue_id] = weakref.ref(queue, cleanup)

        logger.info(f"Created stream queue: {queue_id}")
        return queue_id

    def get_queue(self, queue_id: str) -> Optional[asyncio.Queue]:
        """
        Get queue by ID.

        Args:
            queue_id: The queue identifier

        Returns:
            The queue instance or None if not found
        """
        return self._queues.get(queue_id)

    def cleanup_queue(self, queue_id: str):
        """
        Manually clean up a queue when thread ends.

        Args:
            queue_id: The queue identifier to cleanup
        """
        self._cleanup_queue(queue_id)

    def _cleanup_queue(self, queue_id: str):
        """Internal cleanup method"""
        if queue_id in self._queues:
            del self._queues[queue_id]
            logger.info(f"Cleaned up stream queue: {queue_id}")

        if queue_id in self._queue_refs:
            del self._queue_refs[queue_id]

    def get_active_queues_count(self) -> int:
        """Get the number of active queues (for monitoring)"""
        return len(self._queues)

    async def put_event(self, queue_id: str, event: dict):
        """
        Put an event into the specified queue.

        Args:
            queue_id: The queue identifier
            event: The event data to put
        """
        queue = self.get_queue(queue_id)
        if queue:
            await queue.put(event)
        else:
            logger.warning(f"Queue {queue_id} not found when trying to put event")

    async def get_event(self, queue_id: str, timeout: float = 1.0) -> Optional[dict]:
        """
        Get an event from the specified queue with timeout.

        Args:
            queue_id: The queue identifier
            timeout: Timeout in seconds

        Returns:
            Event data or None if timeout or queue not found
        """
        queue = self.get_queue(queue_id)
        if not queue:
            return None

        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None