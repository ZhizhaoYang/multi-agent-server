from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Annotated, Any
import operator
from pydantic import BaseModel

from app.AI.workflows.models.chat_state import ChatState
from app.web_base.services.chat_services import ChatService


class ChatRequest(BaseModel):
    thread_id: str
    user_input: str
    # role: str = None


class ChatResponse(BaseModel):
    thread_id: str
    response: str
    error: Annotated[List[str], operator.add]
    workflow_queue: Annotated[dict[str, Any] | Any, operator.add]



router = APIRouter()


@router.get("/chat", status_code=200)
async def chat(thread_id: str, user_input: str):
    print("request params ==>", {"thread_id": thread_id, "user_input": user_input})
    service = ChatService()

    return StreamingResponse(
        service.generate_response(user_input),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

    # try:
    #     res = await service.generate_response(
    #         user_input=request.user_input
    #     )

    #     response = res['messages'][-1].content

    #     return ChatResponse(
    #         thread_id=request.thread_id,
    #         response=response,
    #         error=[],
    #         workflow_queue=res,
    #     )

    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))
