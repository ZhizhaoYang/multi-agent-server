from langchain_core.messages import HumanMessage

from app.utils.logger import logger
from app.AI.workflows.graph.main_graph import graph as main_graph
from app.AI.workflows.models.chat_state import ChatState

class ChatService:
    async def generate_response(self, user_input: str):
        state = ChatState(
            query=user_input,
            messages=[HumanMessage(content=user_input)],
            nodes_history=[],
            nodes_count=0,
        )

        result = await main_graph.ainvoke(state)
        # logger.info("**** service result ****")
        # logger.info(result)
        return result
