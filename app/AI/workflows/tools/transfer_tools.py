from app.AI.workflows.models.chat_state import ChatError
from datetime import datetime, timezone

def build_erros(e: Exception, node_name: str) -> ChatError:
    return ChatError(
        node=node_name,
        error=str(e),
        type=type(e).__name__,
        timestamp=datetime.now(timezone.utc).isoformat()
    )