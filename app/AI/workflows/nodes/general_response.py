from langgraph.types import Command
from langchain_core.messages import AIMessage
from typing import Literal

from app.AI.workflows.models.chat_state import ChatState
from app.utils.logger import logger
from app.AI.workflows.agents.general_response_agent import general_response_agent
from app.AI.workflows.constants import NodeNames

async def general_response_node(state: ChatState) -> Command[NodeNames]:
    current_node = NodeNames.GENERAL_RESPONSE.value
    logger.info("**** general_response_node ****")
    logger.info(state)
    result = await general_response_agent.ainvoke(state)
    content = result["messages"][-1].content
    final_response = f'''
    No suitable expert found.
    Here is the response from the general response agent:

    {content}
    '''
    goto = NodeNames.SUPERVISOR.value

    return Command(
        update={
            "messages": [
                AIMessage(content=final_response, name="general_response")
            ],
            # "nodes_history": current_node,
            "nodes_count": state.get("nodes_count") + 1,
        },
        goto=goto,
    )
