from langchain_core.messages import HumanMessage

from app.web_base.models.API_models import APIRequest
from app.AI.supervisor_workflow.shared.models.Chat import ChatState
from app.AI.supervisor_workflow.head_quarter import main_graph
from app.utils.logger import logger

class ChatService:
    def __init__(self, request: APIRequest):
        self.state = ChatState(
            user_query=request.user_query,
            messages=[HumanMessage(content=request.user_query)],
            final_output="",
            errors=[],
        )

    async def run(self):
        logger.info(f"!! ChatService state: {self.state} !!")
        response = await main_graph.ainvoke(self.state)

        logger.info(f"ChatService response: {response}")
        return response