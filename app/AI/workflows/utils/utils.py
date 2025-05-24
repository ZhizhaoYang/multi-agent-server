from app.AI.workflows.models.chat_state import ChatGraphContext
from app.web_base.models.API_models import APIRequest

def from_request_to_context(request: APIRequest) -> ChatGraphContext:
    """Transform API input into execution context"""
    return ChatGraphContext(
        user_query=request.user_query,
        thread_id=request.thread_id,
        # conversation_id=request.conversation_id or f"conv_{uuid4().hex[:20]}"
    )
