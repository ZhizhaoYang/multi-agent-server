from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import asyncio
from langchain_core.runnables import Runnable
import json

from app.web_base.models.API_models import APIRequest
from app.web_base.services.chat_service import ChatService
from app.utils.logger import logger

router = APIRouter()

class SSEMessage:
    def __init__(self, data, event=None, id=None):
        self.data = data
        self.event = event
        self.id = id

    def __str__(self):
        lines = []
        if self.event: lines.append(f"event: {self.event}")
        if self.id:    lines.append(f"id: {self.id}")
        lines.append(f"data: {json.dumps(self.data)}")
        return "\n".join(lines) + "\n\n"

# @router.get("/chat-stream", status_code=200)
# async def chat_stream_handler(request: APIRequest = Depends()):
#     chat_service = ChatService(request)

#     return StreamingResponse(
#         chat_service.run_chat_service(),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#             "X-Accel-Buffering": "no"
#         }
#     )

@router.get("/chat-test", status_code=200)
async def chat_test_handler(request: APIRequest = Depends()):
    chat_service = ChatService(request)
    return await chat_service.run()