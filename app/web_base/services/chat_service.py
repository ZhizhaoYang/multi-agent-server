from langchain_core.runnables import RunnableConfig
from typing import Optional
import json

from app.web_base.models.API_models import APIRequest
from app.AI.supervisor_workflow.shared.models.Chat import UserContext
from app.AI.supervisor_workflow.head_quarter import main_graph


class ChatService:
    def __init__(self, request: APIRequest, user_context: Optional[UserContext] = None):
        self.user_query = request.user_query
        self.thread_id = request.thread_id

        # Store user context with proper thread_id
        self.user_context = user_context or UserContext(
            user_id="123",
            user_role="admin",
            preferred_language="en",
            thread_id=self.thread_id,
        )

    def handle_messages_format(self, chunk_text: str, chunk_type: str, **kwargs):
        data = {"chunk": chunk_text, "type": chunk_type}
        # Add additional data for thought messages
        data.update(kwargs)
        final_Data = f"data: {json.dumps(data)}\n\n"
        return final_Data

    async def run(self):
        """
        Run the chat service with conversation history preservation.

        Process:
        1. Create config with thread_id for checkpointer
        2. Checkpointer automatically loads existing conversation history
        3. add_messages reducer merges new user message with existing messages
        4. Workflow processes with full conversation context
        5. Stream chunks during execution + yield final state when complete
        """
        config: RunnableConfig = {
            "configurable": {
                "thread_id": self.thread_id,
                "user_context": self.user_context,
            }
        }

        input_data = {
            "user_query": self.user_query,
        }

        print('--- streaming chunks --- ')
        # Stream chunks during execution
        async for chunk in main_graph.astream(
            input_data,
            config=config,
            stream_mode=["custom"],
        ):
            result = None

            print(chunk)

            if chunk and isinstance(chunk, tuple) and len(chunk) > 0:
                stream_type = chunk[0]  # stream mode name
                stream_content = chunk[1]  # stream content

                # handle custom stream mode
                if stream_type == "custom":
                    # Handle different types of custom streams
                    message_type = stream_content.get('type', 'final_output')

                    if message_type == 'thought':
                        # Handle character-by-character thought stream
                        thought_content = stream_content.get('thought_content', '')
                        if thought_content:  # Only stream if there's actual content (not empty)
                            result = self.handle_messages_format(
                                thought_content,
                                'thought',
                                source=stream_content.get('source', ''),
                                segment_id=stream_content.get('segment_id', 0),  # Character position
                                timestamp=stream_content.get('timestamp', '')
                            )
                            yield result

                    elif message_type == 'thought_complete':
                        # Handle thought completion marker
                        result = self.handle_messages_format(
                            "",  # Empty content for completion
                            'thought_complete',
                            source=stream_content.get('source', ''),
                            segment_id=stream_content.get('segment_id', 0),  # Total character count
                            total_length=stream_content.get('total_length', 0)
                        )
                        yield result

                    else:
                        # Handle regular final_output stream
                        final_output_str = stream_content.get('final_output', '')
                        if final_output_str:
                            result = self.handle_messages_format(final_output_str, 'final_output')
                            yield result

        # After streaming completes, get the final complete state
        final_state = await main_graph.aget_state(config)
        result = {
            "thread_id": self.thread_id,
            "final_output": final_state.values.get("final_output", ""),
        }
        yield f"data: {json.dumps(result)}\n\n"
