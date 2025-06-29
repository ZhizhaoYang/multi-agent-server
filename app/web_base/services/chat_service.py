from langchain_core.runnables import RunnableConfig
from typing import Optional
import json
import asyncio

from app.web_base.models.API_models import APIRequest
from app.AI.supervisor_workflow.shared.models.Chat import UserContext, ChatState
from app.AI.supervisor_workflow.head_quarter import main_graph
from app.utils.stream_queue_manager import StreamQueueManager
from app.AI.supervisor_workflow.shared.models.stream_models import create_stream_consumer
from app.utils.logger import logger

class ChatService:
    def __init__(self, request: APIRequest, user_context: Optional[UserContext] = None):
        self.user_query = request.user_query
        self.thread_id = request.thread_id

        self.user_context = user_context or UserContext(
            user_id="123",
            user_role="admin",
            preferred_language="en",
            thread_id=self.thread_id,
        )

    def handle_messages_format(self, chunk_text: str, chunk_type: str, **kwargs):
        data = {"chunk": chunk_text, "type": chunk_type}
        data.update(kwargs)
        final_Data = f"data: {json.dumps(data)}\n\n"
        return final_Data

    def _convert_queue_event_to_format(self, event):
        """Convert StreamEvent from queue to the expected client format"""
        if event.event_type == "thought":
            return self.handle_messages_format(
                event.content,
                'thought',
                source=event.source,
                segment_id=event.segment_id,
                timestamp=event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp)
            )
        elif event.event_type == "thought_complete":
            return self.handle_messages_format(
                "",  # Empty content for completion
                'thought_complete',
                source=event.source,
                segment_id=event.segment_id,
                total_length=event.metadata.get('total_length', 0)
            )
        elif event.event_type == "progress":
            return self.handle_messages_format(
                event.content,
                'progress',
                source=event.source,
                progress_percent=event.metadata.get('progress_percent', 0)
            )
        elif event.event_type == "result":
            return self.handle_messages_format(
                event.content,
                'result',
                source=event.source
            )
        elif event.event_type == "error":
            return self.handle_messages_format(
                event.content,
                'error',
                source=event.source
            )
        else:
            # Default handling for unknown event types
            return self.handle_messages_format(
                event.content,
                event.event_type,
                source=event.source,
                segment_id=event.segment_id
            )

    async def run(self):
        """Run the chat service with conversation history preservation and real-time streaming."""
        queue_manager = StreamQueueManager.get_instance()
        queue_id = queue_manager.create_queue(self.thread_id)

        config: RunnableConfig = {
            "configurable": {
                "thread_id": self.thread_id,
                "user_context": self.user_context,
            }
        }

        input_data = ChatState(
            user_query=self.user_query,
            stream_queue_id=queue_id
        )

        stream_consumer = create_stream_consumer(queue_id)

        async def graph_event_generator():
            """Generate events from the main graph"""
            try:
                async for chunk in main_graph.astream(
                    input_data,
                    config=config,
                    stream_mode=["custom"],
                ):
                    if chunk and isinstance(chunk, tuple) and len(chunk) > 0:
                        stream_type = chunk[0]
                        stream_content = chunk[1]

                        if stream_type == "custom":
                            message_type = stream_content.get('type', 'final_output')

                            if message_type == 'thought':
                                thought_content = stream_content.get('thought_content', '')
                                if thought_content:
                                    result = self.handle_messages_format(
                                        thought_content,
                                        'thought',
                                        source=stream_content.get('source', ''),
                                        segment_id=stream_content.get('segment_id', 0),
                                        timestamp=stream_content.get('timestamp', '')
                                    )
                                    yield ("graph", result)

                            elif message_type == 'thought_complete':
                                result = self.handle_messages_format(
                                    "",
                                    'thought_complete',
                                    source=stream_content.get('source', ''),
                                    segment_id=stream_content.get('segment_id', 0),
                                    total_length=stream_content.get('total_length', 0)
                                )
                                yield ("graph", result)

                            else:
                                final_output_str = stream_content.get('final_output', '')
                                if final_output_str:
                                    result = self.handle_messages_format(final_output_str, 'final_output')
                                    yield ("graph", result)
            except Exception as e:
                logger.error(f"Error in graph streaming: {e}")

        internal_queue = asyncio.Queue()

        async def queue_consumer_task():
            """Background task that puts queue events into internal queue"""
            try:
                async for event in stream_consumer.consume_events(timeout_per_event=0.1):
                    result = self._convert_queue_event_to_format(event)
                    if result:
                        await internal_queue.put(("queue", result))
            except Exception as e:
                logger.error(f"Error consuming queue events: {e}")
            finally:
                await internal_queue.put(("queue_done", None))

        async def graph_consumer_task():
            """Background task that puts graph events into internal queue"""
            try:
                async for source, graph_event in graph_event_generator():
                    if graph_event:
                        await internal_queue.put(("graph", graph_event))
            except Exception as e:
                logger.error(f"Error in graph streaming: {e}")
            finally:
                await internal_queue.put(("graph_done", None))

        queue_task = asyncio.create_task(queue_consumer_task())
        graph_task = asyncio.create_task(graph_consumer_task())

        try:
            graph_done = False
            queue_done = False

            while not (graph_done and queue_done):
                try:
                    source, event_data = await asyncio.wait_for(internal_queue.get(), timeout=0.1)

                    if source == "graph_done":
                        graph_done = True
                    elif source == "queue_done":
                        queue_done = True
                    elif event_data:
                        yield event_data

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error getting event from internal queue: {e}")
                    break

        except Exception as e:
            logger.error(f"Error in real-time streaming: {e}")
        finally:
            for task in [queue_task, graph_task]:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            queue_manager.cleanup_queue(queue_id)

        final_state = await main_graph.aget_state(config)
        result = {
            "thread_id": self.thread_id,
            "final_output": final_state.values.get("final_output", ""),
        }
        yield f"data: {json.dumps(result)}\n\n"
