from fastapi import APIRouter, HTTPException
from typing import TypedDict, List, Annotated
import operator
from pydantic import BaseModel

from app.AI.workflows.models.chat_state import ChatState
from app.web_base.services.chat_services import ChatService


class ChatRequest(BaseModel):
    thread_id: str
    user_input: str
    # role: str = None


class ChatResponse(ChatState):
    thread_id: str
    response: str
    error: Annotated[List[str], operator.add]


router = APIRouter()


@router.post("/chat", status_code=200)
async def chat(request: ChatRequest):
    service = ChatService()

    try:
        res = await service.generate_response(
            user_input=request.user_input
        )

        response = res['messages'][-1].content

        return ChatResponse(
            thread_id=request.thread_id,
            response=response,
            error=[],
            **res,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
