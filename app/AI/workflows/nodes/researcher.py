from langgraph.types import Command
from langchain_core.messages import AIMessage
from typing import Literal, cast

from app.AI.workflows.models.chat_state import ChatWorkflowState
from app.AI.workflows.agents.research_agent import research_agent
from app.utils.logger import logger
from app.AI.workflows.constants import NodeNames


async def researcher_node(state: ChatWorkflowState) -> Command[NodeNames]:
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

    # Add this node to visited workers
    visited_workers = set(state.visited_workers)
    visited_workers.add(current_node)

    return Command(
        update={
            "messages": [
                AIMessage(content=result["messages"]
                          [-1].content, name="researcher")
            ],
            "nodes_history": [current_node],
            "visited_workers": visited_workers,
        },
        goto=goto,
    )
