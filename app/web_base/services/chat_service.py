from langchain_core.runnables import RunnableConfig
from typing import Optional, AsyncGenerator
import asyncio

from app.web_base.models.API_models import APIRequest
from app.AI.supervisor_workflow.shared.models.Chat import UserContext, ChatState
from app.utils.logger import logger
from app.utils.stream_queue_manager import StreamQueueManager
from app.AI.supervisor_workflow.shared.models.stream_models import create_stream_consumer
from .event_converter import StreamEventConverter


class ChatService:
    """Clean, focused chat service with lightweight event conversion"""

    def __init__(self, request: APIRequest, user_context: Optional[UserContext] = None):
        self.user_query = request.user_query
        self.thread_id = request.thread_id
        self.user_context = user_context or UserContext(
            user_id="123",
            user_role="admin",
            preferred_language="en",
            thread_id=self.thread_id,
        )
        # Use lightweight event converter
        self.event_converter = StreamEventConverter

    def _get_main_graph(self):
        """Lazy import of main_graph to avoid initialization issues"""
        from app.AI.supervisor_workflow.head_quarter import main_graph
        return main_graph

    def _create_config(self) -> RunnableConfig:
        """Create the configuration for the graph execution"""
        return {
            "configurable": {
                "thread_id": self.thread_id,
                "user_context": self.user_context,
            }
        }

    def _create_input_data(self, queue_id: str) -> ChatState:
        """Create the input data for the graph"""
        return ChatState(
            user_query=self.user_query,
            stream_queue_id=queue_id
        )

    async def _get_final_state(self, config: RunnableConfig) -> str:
        """Get the final state after graph completion"""
        try:
            main_graph = self._get_main_graph()
            final_state = await main_graph.aget_state(config)
            return final_state.values.get("final_output", "")
        except Exception as e:
            logger.error(f"Error getting final state: {e}")
            return ""

    async def _create_queue_events(self, stream_consumer) -> AsyncGenerator[tuple[str, str], None]:
        """Generate events from the queue consumer"""
        try:
            async for event in stream_consumer.consume_events(timeout_per_event=0.1):
                result = self.event_converter.convert_queue_event(event)
                if result:
                    yield ("queue", result)
        except Exception as e:
            logger.error(f"Error consuming queue events: {e}")

    async def _create_graph_events(self, graph, input_data: ChatState, config: RunnableConfig) -> AsyncGenerator[tuple[str, str], None]:
        """Generate events from the graph"""
        try:
            async for chunk in graph.astream(
                input_data,
                config=config,
                stream_mode=["custom"],
            ):
                if chunk and isinstance(chunk, tuple) and len(chunk) > 0:
                    stream_type = chunk[0]
                    stream_content = chunk[1]

                    if stream_type == "custom":
                        result = self.event_converter.convert_graph_event(stream_content)
                        if result:
                            yield ("graph", result)
        except Exception as e:
            logger.error(f"Error in graph streaming: {e}")

    async def run(self) -> AsyncGenerator[str, None]:
        """
        Run the chat service with real-time streaming.

        Service controls orchestration, uses lightweight converter for event formatting.
        """
        # Service layer manages queue
        queue_manager = StreamQueueManager.get_instance()
        queue_id = queue_manager.create_queue(self.thread_id)
        stream_consumer = create_stream_consumer(queue_id)

        # Setup configuration and input data
        config = self._create_config()
        input_data = self._create_input_data(queue_id)
        graph = self._get_main_graph()

        # Service layer controls event merging
        internal_queue = asyncio.Queue()

        async def queue_consumer_task():
            """Background task for queue events"""
            try:
                async for source, event_data in self._create_queue_events(stream_consumer):
                    await internal_queue.put((source, event_data))
            except Exception as e:
                logger.error(f"Error in queue consumer task: {e}")
            finally:
                await internal_queue.put(("queue_done", None))

        async def graph_consumer_task():
            """Background task for graph events"""
            try:
                async for source, event_data in self._create_graph_events(graph, input_data, config):
                    await internal_queue.put((source, event_data))
            except Exception as e:
                logger.error(f"Error in graph consumer task: {e}")
            finally:
                await internal_queue.put(("graph_done", None))

        # Service layer orchestrates
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

            # Send final result using converter
            final_output = await self._get_final_state(config)
            final_message = self.event_converter.format_final_result(self.thread_id, final_output)
            yield final_message

        except Exception as e:
            logger.error(f"Error in chat service: {e}")
            error_message = self.event_converter.format_sse_message(
                f"Error: {str(e)}",
                'error'
            )
            yield error_message
        finally:
            # Service layer cleanup
            for task in [queue_task, graph_task]:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            queue_manager.cleanup_queue(queue_id)

