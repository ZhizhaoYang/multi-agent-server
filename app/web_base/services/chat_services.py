from langchain_core.messages import HumanMessage, AIMessageChunk
import json
import asyncio
from typing import AsyncGenerator

from app.utils.logger import logger
from app.AI.workflows.graph.main_graph import graph as main_graph
from app.AI.workflows.models.chat_state import ChatWorkflowState, ChatGraphContext
from app.web_base.models.API_models import APIRequest
from app.utils.stream_tools import stream_generator
from app.AI.workflows.utils.utils import from_request_to_context


class ChatService:
    def __init__(self, request: APIRequest):
        self.ctx = from_request_to_context(request)
        self.state = ChatWorkflowState(
            messages=[HumanMessage(content=self.ctx.user_query)],
            next_steps=[],
            current_output="",
            errors=[],
        )

    async def run_chat_service(self) -> AsyncGenerator[str, None]:
        # print("----------------------------------- run_chat_service -----------------------------------")
        # print("----------------------------------- self.ctx -----------------------------------")
        # print(self.ctx)
        # print("----------------------------------- self.state -----------------------------------")
        # print(self.state)
        # return stream_generator(test_graph, self.state, stream_mode="messages")
        async for chunk in main_graph.astream(
            self.state,
            stream_mode=["messages", "updates"],
            config={"configurable": {"thread_id": self.ctx.thread_id}}
        ):

            # print("\n")
            # logger.info(
            #     "----------------------------------- chunk -----------------------------------")
            # logger.info(chunk)

            chunk_text = ""
            node_path = []
            if chunk and isinstance(chunk, tuple) and len(chunk) > 0:
                # Will be either "messages" or "updates"
                stream_type = chunk[0]
                stream_content = chunk[1]

                if stream_type == "messages" and stream_content[0] and isinstance(stream_content[0], AIMessageChunk):
                    chunk_text = stream_content[0].content
                elif stream_type == "updates" and stream_content:
                    if hasattr(stream_content, 'next_steps') and isinstance(stream_content.next_steps, list):
                        node_path = [node.name for node in stream_content.next_steps if hasattr(node, 'name')]

            data = {"chunk": chunk_text, "type": stream_type, "node_path": node_path}
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.01)

        # Send done event to signal the stream is complete
        yield f"event: done\ndata: {{}}\n\n"
