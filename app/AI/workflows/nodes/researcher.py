from langgraph.types import Command
from langchain_core.messages import AIMessage
from typing import Literal, cast

from app.AI.workflows.models.chat_state import ChatState
from app.AI.workflows.agents.research_agent import research_agent
from app.utils.logger import logger
from app.AI.workflows.constants import NodeNames


async def researcher_node(state: ChatState) -> Command[NodeNames]:
    current_node = NodeNames.RESEARCHER.value

    logger.info("**** researcher_node ****")
    logger.info(state)
    try:
        result = await research_agent.ainvoke(state)
        logger.info("**** researcher_node result ****")
        logger.info(result)
        goto = NodeNames.SUPERVISOR.value
    except Exception as e:
        logger.error(e)
        raise e

    return Command(
        update={
            "messages": [
                AIMessage(content=result["messages"]
                          [-1].content, name="researcher")
            ],
            # "nodes_history": current_node,
            "nodes_count": state.get("nodes_count") + 1,
        },
        goto=goto,
    )
