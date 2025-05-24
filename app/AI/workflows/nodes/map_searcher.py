from langgraph.types import Command
from langchain_core.messages import AIMessage
from typing import Literal

from app.AI.workflows.models.chat_state import ChatWorkflowState
from app.utils.logger import logger
from app.AI.workflows.agents.map_searcher_agent import get_map_searcher_agent
from app.AI.workflows.constants import NodeNames


async def map_searcher_node(state: ChatWorkflowState) -> Command[NodeNames]:
    current_node = NodeNames.MAP_SEARCHER.value
    logger.info("**** map_searcher_node ****")
    logger.info(state)
    try:
        # Get the agent instance
        agent = await get_map_searcher_agent()

        if agent is None:
            raise Exception("Map searcher agent is not initialized")

        result = await agent.ainvoke(state)
        goto = NodeNames.SUPERVISOR.value
    except Exception as e:
        logger.info("**** map_searcher_node error ****")
        logger.error(e)
        raise e

    return Command(
        update={
            "messages": [
                AIMessage(content=result["messages"]
                          [-1].content, name="map-searcher")
            ],
            "nodes_history": [current_node],
            # "nodes_count": state.get("nodes_count") + 1,
        },
        goto=goto,
    )
