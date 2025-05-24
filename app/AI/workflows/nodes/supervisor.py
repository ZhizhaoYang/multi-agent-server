from typing import TypedDict, Any
from langgraph.graph import END
from langgraph.types import Command
from langchain_core.messages import AIMessage
from datetime import datetime, timezone
import json

from app.AI.workflows.models.chat_state import ChatWorkflowState, ChatError
from app.AI.core.llm import LLMFactory, LLMConfig
from app.utils.logger import logger
from app.AI.workflows.constants import NodeNames
from app.AI.workflows.models import ChatNode, ChatNodeType
from app.AI.workflows.tools.transfer_tools import build_erros

ALL_WORKERS = [
    NodeNames.RESEARCHER.value,
    NodeNames.MAP_SEARCHER.value,
    NodeNames.MATH_EXPERT.value,
]

# Formatted members string for the prompt
formatted_members_str = ", ".join(ALL_WORKERS)

system_prompt = f"""
    You are a supervisor tasked with managing a conversation between the following workers: {formatted_members_str}.
    Given the user's request, you must decide which worker(s) should act next.
    Your response must be a JSON object with a key "next", and the value must be a list of strings representing the names of the nodes to call.
    Examples:
    - To call a single worker (e.g., Worker_Node_1): {{\"next\": [\"Worker_Node_1\"]}}
    - To call multiple workers in parallel (e.g., Worker_Node_1 and Worker_Node_2): {{\"next\": [\"Worker_Node_1\", \"Worker_Node_2\"]}}
    - If none of the available workers ({formatted_members_str}) are suitable for the user's query, route to {NodeNames.GENERAL_RESPONSE.value}: {{\"next\": [\"{NodeNames.GENERAL_RESPONSE.value}\"]}}
    - If all tasks are complete and the process should end: {{\"next\": [\"END\"]}}

    Each worker will perform its task and report its results. You will be called again after they complete their work.
"""


llm = LLMFactory.create_llm(
    LLMConfig(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0.5,
    )
)


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: list[str]


MAX_STEPS = 10  # Set your max steps for safe development


def jump_next_node(state: ChatWorkflowState, goto_nodes: list[str], errors: list[ChatError] = []) -> Command[NodeNames]:



async def supervisor_node(state: ChatWorkflowState) -> Command:
    try:
        if not state.messages:
            raise ValueError("No human query found in the state.")

        # Extract the last message
        last_message = state.messages[-1]

        # Call the LLM with structured output
        response = llm.with_structured_output(Router).invoke(system_prompt, last_message.content)
        # Parse the response

        parsed_output = json.loads(response)

    except Exception as e:
        logger.error(f"Error in supervisor_node: {e}")
        error = ChatError(
            node=NodeNames.SUPERVISOR.value,
            error=str(e),
            type=type(e).__name__,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        return jump_next_node(state, [NodeNames.GENERAL_RESPONSE.value], [error])




