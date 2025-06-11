from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from datetime import datetime, timezone
from typing import Optional

from app.web_base.models.API_models import APIRequest
from app.AI.supervisor_workflow.shared.models.Chat import ChatState, UserContext
from app.AI.supervisor_workflow.head_quarter import main_graph
from app.utils.logger import logger


class ChatService:
    def __init__(self, request: APIRequest, user_context: Optional[UserContext] = None):
        # Create state with top-level core fields (Studio compatible)
        self.state = ChatState(
            thread_id=request.thread_id,
            user_query=request.user_query,
            messages=[HumanMessage(content=request.user_query)],
            final_output="",
            errors=[]
        )

        # Store user context (can be None for simple cases)
        self.user_context = user_context or UserContext(
            user_id="123",
            user_role="admin",
            preferred_language="en",
        )

    async def run(self):
        # Create configuration for thread-based execution with user context
        config: RunnableConfig = {
            "configurable": {
                **self.user_context.model_dump()
            }
        }

        # Run the graph with thread configuration and user context
        response = await main_graph.ainvoke(self.state, config=config)

        logger.info(f"ChatService response: {response}")
        return response
