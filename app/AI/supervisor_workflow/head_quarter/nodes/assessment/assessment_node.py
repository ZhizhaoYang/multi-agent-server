from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.language_models.chat_models import BaseChatModel
import json
from pydantic import ValidationError

from app.AI.supervisor_workflow.shared.models import ChatState
from app.AI.supervisor_workflow.head_quarter.nodes.assessment.prompts import sys_prompt_for_assessment
from app.utils.logger import logger
from app.AI.core.llm import LLMFactory, LLMConfig, LLMProviders
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_Dept, NodeNames_HQ
from app.AI.supervisor_workflow.shared.models.Assessment import LLMAssessmentOutput
from app.AI.supervisor_workflow.head_quarter.dept_registry_center import department_registry

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
    )
)


async def _call_llm_for_assessment(
    llm: BaseChatModel,
    system_prompt_template: SystemMessagePromptTemplate,
    user_query: Optional[str],
    available_departments_str: str
) -> LLMAssessmentOutput:
    try:
        chat_prompt = ChatPromptTemplate.from_messages([system_prompt_template])
        formatted_messages = chat_prompt.format_messages(
            user_query=user_query,
            available_departments=available_departments_str
        )
        response_data = await llm.ainvoke(formatted_messages)

        raw_content = response_data.content

        if not isinstance(raw_content, str):
            error_msg = f"LLM content for assessment is not a string. Received type: {type(raw_content)}. Content: {raw_content}"
            logger.error(error_msg)
            raise TypeError(error_msg)

        content_str = raw_content.strip().strip('```json').strip('```').strip()
        result = LLMAssessmentOutput.model_validate_json(content_str)

        return result

    except Exception as e:
        logger.error(f"Error in _call_llm_for_assessment: {e}")
        raise e


async def assessment_node(state: ChatState) -> Command:
    """
    This node is responsible for assessing the user's query using an injected LLM instance.
    It uses the LLM to:
    1. Understand the user's intent.
    2. Decompose the user's query into smaller, actionable tasks.
    3. Provide an overall summary of the user's request.
    4. Suggest an appropriate department to handle the query.

    Args:
        state: The current ChatState.

    Returns:
        An updated ChatState.
    """

    logger.info(f"!! Assessment node !!")
    current_node = NodeNames_HQ.ASSESSMENT.value
    new_updates = {}

    try:

        llm_assessment_output = await _call_llm_for_assessment(
            llm=llm,
            system_prompt_template=sys_prompt_for_assessment,
            user_query=state.user_query,
            available_departments_str=AVAILABLE_DEPARTMENTS_STRING
        )

        new_updates["assessment_report"] = llm_assessment_output

        return Command(
            update={
                **new_updates,
            },
            goto=NodeNames_HQ.SUPERVISOR.value
        )
    except Exception as e:
        new_error = state.build_error(e, current_node)
        new_updates["errors"] = [new_error]

        return Command(
            update={
                **new_updates,
                "assessment_report": None,
            },
            goto=END
        )
