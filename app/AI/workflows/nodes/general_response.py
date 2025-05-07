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

    # Template for the response
    template = '''
    No suitable expert found.
    Here is the response from the general response agent:

    {content}
    '''

    # Stream the response
    async for chunk in general_response_agent.astream(
        state,
        stream_mode="messages"
    ):
        logger.info("**** general_response_node chunk ****")
        logger.info(chunk)
        if chunk and "messages" in chunk and chunk["messages"]:
            content = chunk["messages"][-1].content
            response = template.format(content=content)
            return Command(
                update={
                    "messages": [
                        AIMessage(content=response, name="general_response")
                    ],
                    "nodes_history": [current_node],
                    "nodes_count": state.get("nodes_count") + 1,
                },
                goto=NodeNames.SUPERVISOR.value,
            )

    # If no chunks were received, return a default response
    return Command(
        update={
            "messages": [
                AIMessage(content="No response received from the general response agent.", name="general_response")
            ],
            "nodes_history": [current_node],
            "nodes_count": state.get("nodes_count") + 1,
        },
        goto=NodeNames.SUPERVISOR.value,
    )
