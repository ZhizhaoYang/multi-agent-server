from typing import Optional, List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AnyMessage
import asyncio
from langchain_core.runnables import RunnableConfig
# Removed StreamWriter imports - now using queue-based streaming

from app.AI.supervisor_workflow.shared.models import ChatState
from app.AI.supervisor_workflow.head_quarter.nodes.assessment.prompts import sys_prompt_for_assessment
from app.utils.logger import logger
from app.AI.supervisor_workflow.shared.utils.logUtils import print_current_node
from app.AI.core.llm import LLMFactory, LLMConfig, LLMProviders
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_HQ
from app.AI.supervisor_workflow.shared.models.Assessment import LLMAssessmentOutput
from app.AI.supervisor_workflow.head_quarter.dept_registry_center import department_registry

CURRENT_NODE_NAME = NodeNames_HQ.ASSESSMENT.value

def conver_registered_dept_str() -> str:
    _available_depts = department_registry.get_all_departments()
    formatted_lines = []
    for dept_info in _available_depts.values():
        formatted_lines.append(f"{dept_info.department_name}: {dept_info.description}")
    return "\n".join(formatted_lines)

AVAILABLE_DEPARTMENTS_STRING: str = conver_registered_dept_str()


llm = LLMFactory.create_llm(
    LLMConfig(
        provider=LLMProviders.DEEPSEEK.value,
        model="deepseek-chat",
        temperature=1.0,
        model_kwargs={
            "response_format": {
                "type": "json_object"
            }
        }
    )
)

def format_conversation_history(messages: List[AnyMessage]) -> str:
    """Format conversation history for the assessment prompt"""
    if not messages:
        return "No previous conversation."

    # Format recent messages for context (last 10 messages)
    recent_messages = messages[-10:] if len(messages) > 10 else messages
    formatted_history = []

    for msg in recent_messages:
        if hasattr(msg, 'type'):
            msg_type = msg.type
        else:
            msg_type = type(msg).__name__.replace('Message', '').lower()

        content = str(msg.content) if hasattr(msg, 'content') else str(msg)
        formatted_history.append(f"{msg_type.capitalize()}: {content}")

    return "\n".join(formatted_history)

async def _call_llm_for_assessment(
    llm: BaseChatModel,
    system_prompt_template: SystemMessagePromptTemplate,
    user_query: Optional[str],
    available_departments_str: str,
    conversation_history: str = "",
) -> LLMAssessmentOutput:
    try:
        chat_prompt = ChatPromptTemplate.from_messages([
            system_prompt_template
        ])
        formatted_messages = chat_prompt.format_messages(
            user_query=user_query,
            available_departments=available_departments_str,
            conversation_history=conversation_history
        )


        response_data = await llm.ainvoke(formatted_messages)
        raw_content = response_data.content

        if not isinstance(raw_content, str):
            error_msg = f"LLM content for assessment is not a string. Received type: {type(raw_content)}. Content: {raw_content}"
            logger.error(error_msg)
            raise TypeError(error_msg)

        content_str = raw_content.strip()
        result = LLMAssessmentOutput.model_validate_json(content_str)

        return result

    except Exception as e:
        raise e

async def assessment_node(state: ChatState, config: RunnableConfig) -> Command:
    """
    Enhanced assessment node with state composition and thread context awareness.

    This node:
    1. Uses the new state composition pattern (core, supervisor, thread, workflow)
    2. Builds context-aware prompts using thread history
    3. Updates thread state with new assessment information
    4. Maintains conversation continuity across thread interactions
    """
    print_current_node(CURRENT_NODE_NAME)
    logger.info(f"!! Assessment node state: {state.model_dump_json(indent=2)} !!")

    publisher = state.get_stream_publisher()
    if publisher is not None:
        await publisher.publish_thought(
            content="Generating assessment report...",
            source=NodeNames_HQ.ASSESSMENT.value,
            segment_id=1
        )
        await asyncio.sleep(0.01)

    # full_ctx_messages = state.messages + [HumanMessage(content=state.user_query, id=str(uuid.uuid4()))]
    new_updates: Dict[str, Any] = {
        # "messages": full_ctx_messages
        # "stream_writer": stream_writer
    }

    try:
        # Format conversation history for assessment context
        conversation_history = format_conversation_history(state.messages)

        llm_assessment_output = await _call_llm_for_assessment(
            llm=llm,
            system_prompt_template=sys_prompt_for_assessment,
            user_query=state.user_query,
            available_departments_str=AVAILABLE_DEPARTMENTS_STRING,
            conversation_history=conversation_history,
        )

        logger.info(f"!! Assessment output: {llm_assessment_output.model_dump_json(indent=2)} !!")


        if publisher is not None:
            for i, char in enumerate(llm_assessment_output.assessment_summary):
                await publisher.publish_thought(
                    content=char,
                    source=NodeNames_HQ.ASSESSMENT.value,
                    segment_id=i
                )
                await asyncio.sleep(0.01)

            await asyncio.sleep(0.05)
            await publisher.publish_thought_complete(
                source=NodeNames_HQ.ASSESSMENT.value,
                segment_id=len(llm_assessment_output.assessment_summary)
            )

        new_updates["assessment"] = state.assessment.model_copy(update={
            "assessment_report": llm_assessment_output,
            "assessment_summary": llm_assessment_output.assessment_summary,
        })

        # Note: stream_queue_id is already part of the state, no need to update

        return Command(
            update=new_updates,
            goto=NodeNames_HQ.SUPERVISOR.value
        )

    except Exception as e:
        logger.error(f"!! Assessment node error: {e} !!")
        new_error = state.build_error(e, CURRENT_NODE_NAME)

        # Update core state with error
        new_updates["errors"] = [new_error]

        # Update supervisor state to indicate failure
        new_updates["assessment"] = state.assessment.model_copy(update={
            "assessment_report": None,

        })

        return Command(
            update=new_updates,
            goto=END
        )
