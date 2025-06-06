# from langchain_core.messages import HumanMessage, AIMessageChunk
# import json
# import asyncio
# from typing import AsyncGenerator

# from app.utils.logger import logger
# from app.AI.workflows.graph.main_graph import graph as main_graph
# from app.AI.workflows.models.chat_state import ChatWorkflowState, ChatGraphContext
# from app.web_base.models.API_models import APIRequest
# from app.utils.stream_tools import stream_generator
# from app.AI.workflows.utils.utils import from_request_to_context


# class ChatService:
#     def __init__(self, request: APIRequest):
#         self.ctx = from_request_to_context(request)
#         self.state = ChatWorkflowState(
#             user_query=self.ctx.user_query,
#             messages=[HumanMessage(content=self.ctx.user_query)],
#             walk_through_nodes=[],
#             final_output="",
#             errors=[],
#         )

#     def handle_mode_messages(self, stream_content: AIMessageChunk):
#             chunk_text = stream_content.content
#             data = {"chunk": chunk_text, "type": "messages"}
#             final_Data = f"data: {json.dumps(data)}\n\n"
#             return final_Data

#     def handle_mode_values(self, state: ChatWorkflowState):
#         # logger.info("**** stream_content - state ****")
#         # logger.info(state)

#         walk_through_nodes_names = []
#         # Check if state has 'walk_through_nodes', it's not None, and is a list.
#         if hasattr(state, 'walk_through_nodes') and state.walk_through_nodes is not None and isinstance(state.walk_through_nodes, list):
#             walk_through_nodes_names = [node.name for node in state.walk_through_nodes if hasattr(node, 'name')]

#         data = {"chunk": "", "type": "values", "walk_through_nodes": walk_through_nodes_names}
#         final_Data = f"data: {json.dumps(data)}\n\n"
#         # logger.info("**** handle_mode_values - final_Data ****")
#         # logger.info(final_Data)
#         return final_Data

#     async def run_chat_service(self) -> AsyncGenerator[str, None]:
#         async for chunk in main_graph.astream(
#             self.state,
#             stream_mode=["messages", "custom"],
#             config={"configurable": {"thread_id": self.ctx.thread_id}}
#         ):
#             result = None

#             if chunk and isinstance(chunk, tuple) and len(chunk) > 0:
#                 stream_type = chunk[0] # stream mode
#                 stream_content = chunk[1] # stream content

#                 # hanlde messages mode
#                 if stream_type == "messages" and stream_content[0] and isinstance(stream_content[0], AIMessageChunk):
#                     result = self.handle_mode_messages(stream_content[0])
#                     # logger.info(f"ChatService result: {result}")
#                     yield result

#                 # handle updates mode
#                 elif stream_type == "values" and stream_content:
#                     result = self.handle_mode_values(stream_content)
#                     yield result

#             await asyncio.sleep(0.01)

#         # Send done event to signal the stream is complete
#         yield f"event: done\ndata: {{}}\n\n"
