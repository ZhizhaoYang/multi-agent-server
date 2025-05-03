from langgraph.types import Command
from langchain_core.messages import AIMessage
from typing import Literal

from app.AI.workflows.models.chat_state import ChatState
from app.utils.logger import logger
from app.AI.workflows.constants import NodeNames
from app.AI.workflows.agents.map_agent import get_map_agent
from app.AI.workflows.constants import NodeNames


async def map_searcher_node(state: ChatState) -> Command[NodeNames]:
    current_node = NodeNames.MAP_SEARCHER.value

    try:
        # Get the agent instance
        agent = await get_map_agent()
        # Use the agent to invoke with the state
        result = await agent.ainvoke(state)
        logger.info("**** coder_node result ****")
        logger.info(result)
        goto = NodeNames.SUPERVISOR.value
    except Exception as e:
        logger.error(e)
        raise e

    return Command(
        update={
            "messages": [
                AIMessage(content=result["messages"]
                          [-1].content, name="map-searcher")
            ],
            # "nodes_history": current_node,
        "nodes_count": state.get("nodes_count") + 1,
        },
        goto=goto,
    )
