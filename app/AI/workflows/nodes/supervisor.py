from typing import TypedDict
from langgraph.graph import END
from langgraph.types import Command
from langchain_core.messages import AIMessage, AnyMessage

from app.AI.workflows.models.chat_state import ChatState
from app.AI.core.llm import LLMFactory, LLMConfig
from app.utils.logger import logger
from app.AI.workflows.constants import NodeNames

members = [
    NodeNames.RESEARCHER.value,
    NodeNames.MAP_SEARCHER.value,
]

system_prompt = """
    You are a supervisor tasked with managing a conversation between the following workers: {members}.
    Given the following user request, respond with the worker to act next.
    Each worker will perform a task and respond with their results and status.
    If you don't think any workers are needed, respond with {NodeNames.GENERAL_RESPONSE.value}.
    When finished, respond with END.
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

    next: NodeNames


async def supervisor_node(state: ChatState) -> Command[NodeNames]:
    current_node = NodeNames.SUPERVISOR.value

    try:
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage):
            return Command(
                update={
                    "nodes_history": [current_node],
                    "nodes_count": state.get("nodes_count") + 1,
                },
                goto=END
            )

        logger.info("**** supervisor_node ****")
        logger.info(state)
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            *state["messages"],
        ]

        response = await llm.with_structured_output(Router).ainvoke(messages)
        goto = response["next"]
        logger.info("**** goto ****")
        logger.info(goto)
        # logger.info(type(goto))
        # if goto == NodeNames.END.value:
        #     goto = END

        return Command(
            update={
                "nodes_history": [current_node],
                "nodes_count": state.get("nodes_count") + 1,
            },
            goto=END if goto == "END" else goto
        )

    except Exception as e:
        logger.info("**** supervisor_node error ****")
        logger.error(e)
        return Command(
            update={
                "nodes_history": [current_node],
                "nodes_count": state.get("nodes_count") + 1,
            },
            goto=END
        )
