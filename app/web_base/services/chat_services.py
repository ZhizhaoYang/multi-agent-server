from langchain_core.messages import HumanMessage
import json
import asyncio

from app.utils.logger import logger
from app.AI.workflows.graph.main_graph import graph as main_graph
from app.AI.workflows.models.chat_state import ChatState


class ChatService:
    async def generate_response(self, user_input: str):
        state = ChatState(
            query=user_input,
            messages=[HumanMessage(content=user_input)],
            nodes_history=[],
            nodes_count=0,
        )

        async for chunk in main_graph.astream(state, stream_mode="messages"):
            # Log with proper format
            logger.info(f"chunk: {chunk}")

            # Extract text content from AIMessageChunk
            chunk_text = ""
            if chunk and isinstance(chunk, tuple) and len(chunk) > 0:
                message_chunk = chunk[0]
                if hasattr(message_chunk, 'content'):
                    chunk_text = message_chunk.content

            # Create a JSON-serializable object
            data = {"chunk": chunk_text}
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.01)

        # Send done event to close the connection
        yield f"event: done\ndata: {{}}\n\n"

        # result = await main_graph.ainvoke(state)
        # logger.info("**** service result ****")
        # logger.info(result)
        # return result
