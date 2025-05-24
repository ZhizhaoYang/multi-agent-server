from langgraph.types import Command
from langchain_core.messages import AIMessage

from app.AI.workflows.models.chat_state import ChatWorkflowState
from app.utils.logger import logger
from app.AI.workflows.agents.math_expert_agent import math_expert_agent
from app.AI.workflows.constants import NodeNames
from app.AI.workflows.tools.transfer_tools import build_erros

async def math_expert_node(state: ChatWorkflowState) -> Command[NodeNames]:
    current_node_name = NodeNames.MATH_EXPERT.value
    logger.info(f"**** {current_node_name} ****")
    logger.info(state)

    updated_state_dict = {}
    next_node = NodeNames.SUPERVISOR.value

    try:
        # Invoke the math agent
        agent_response = await math_expert_agent.ainvoke(state)
        logger.info(agent_response)

        # Extract content from agent response
        if "messages" in agent_response and agent_response["messages"]:
            agent_content = agent_response["messages"][-1].content
        else:
            agent_content = "Math agent provided no parsable content."
            logger.warning(
                f"{current_node_name}: No parsable content in agent_response: {agent_response}")

        updated_state_dict["messages"] = [AIMessage(content=agent_content, name=current_node_name)]
        updated_state_dict["current_output"] = agent_content

        # Check for errors reported by the agent itself (if any)
        if agent_response.get("error"):
            error_message = str(agent_response["error"])
            logger.error(
                f"{current_node_name} agent reported error: {error_message}")
            updated_state_dict["errors"] = [error_message]

    except Exception as e:
        logger.error(f"Error in {current_node_name}: {e}")

        error_entry = build_erros(e, current_node_name)

        updated_state_dict["errors"] = [error_entry]
        updated_state_dict["current_output"] = f"Error in {current_node_name}: {str(e)}"

    # Add this node to visited workers
    visited_workers = set(state.visited_workers)
    visited_workers.add(current_node_name)
    updated_state_dict["visited_workers"] = visited_workers

    return Command(
        update=updated_state_dict,
        goto=next_node
    )
