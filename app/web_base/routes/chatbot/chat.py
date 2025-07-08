from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

from app.web_base.models.API_models import APIRequest
from app.web_base.services.chat_service import ChatService

router = APIRouter()


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


@router.post("/chat-test", status_code=200)
async def chat_test_handler(request: APIRequest):
    """Main chat endpoint with conversation history support"""
    chat_service = ChatService(request)

    return StreamingResponse(
        chat_service.run(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.delete("/clear-history", status_code=200)
async def clear_history_handler():
    """Clear all conversation history from SQLite database"""
    from app.AI.supervisor_workflow.shared.utils.checkpointer_manager import clear_sqlite_history

    result = await clear_sqlite_history()
    return result
