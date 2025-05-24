from langgraph.types import Command

from app.AI.workflows.models.chat_state import ChatWorkflowState
from app.utils.logger import logger
from app.AI.workflows.agents.general_response_agent import general_response_agent
from app.AI.workflows.constants import NodeNames
from app.AI.workflows.models.chat_state import ChatNode, ChatNodeType
from app.AI.workflows.tools.transfer_tools import build_erros

template = '''
    No suitable expert found.
    Here is the response from the general response agent:

    {content}
    '''


async def general_response_node(state: ChatWorkflowState) -> Command[NodeNames]:
    logger.info("**** general_response_node 111****")
    logger.info(state)

    current_node = ChatNode(
        name=NodeNames.GENERAL_RESPONSE.value,
        type=ChatNodeType.WORKER,
    )
    last_message = None

    try:
        llm_response = await general_response_agent.ainvoke(state)
        logger.info("**** llm_response ****")
        logger.info(llm_response)
        last_message = llm_response.get("messages", [])[-1]

        response = template.format(content=last_message.content)
        logger.info("**** general_response_node response ****")
        logger.info(response)

        # Add this node to visited workers
        visited_workers = set(state.visited_workers)
        visited_workers.add(current_node.name)

        return Command(
            update={
                "next_steps": [current_node],
                "current_output": response,
                "messages": [last_message],
                "visited_workers": visited_workers,
            },
            goto=NodeNames.SUPERVISOR.value,
        )

    except Exception as e:
        logger.error(f"Error in general_response_node: {e}")
        error = build_erros(e, NodeNames.GENERAL_RESPONSE.value)
        messages_update = []
        if last_message:
            messages_update.append(last_message)

        # Add this node to visited workers even in case of error
        visited_workers = set(state.visited_workers)
        visited_workers.add(current_node.name)

        return Command(
            update={
                "next_steps": [current_node],
                "current_output": "No response received from the general response agent due to an error.",
                "messages": messages_update,
                "errors": [error],
                "visited_workers": visited_workers,
            },
            goto=NodeNames.AGGREGATOR.value
        )
