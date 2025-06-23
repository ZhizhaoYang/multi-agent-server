from langgraph.types import Command

from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage

from app.AI.supervisor_workflow.shared.models import CompletedTask, TaskStatus, NodeNames_Dept
from app.AI.supervisor_workflow.shared.models.Chat import SupervisorState
from app.AI.core.llm import LLMFactory, LLMConfig, LLMProviders
from app.AI.supervisor_workflow.shared.utils.logUtils import print_current_node
from app.AI.supervisor_workflow.departments.utils.errors import node_error_handler
from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput

CURRENT_NODE_NAME = NodeNames_Dept.GENERAL_KNOWLEDGE.value


@node_error_handler(from_department=NodeNames_Dept.GENERAL_KNOWLEDGE)
async def _call_general_knowledge_llm(dept_input: DeptInput) -> str:
    """Call the LLM and return the response content as a string"""
    task = dept_input.task
    supervisor = dept_input.supervisor

    try:
        llm = LLMFactory.create_llm(
            LLMConfig(
                provider=LLMProviders.DEEPSEEK.value,
                model="deepseek-chat",
                temperature=0.5,
            )
        )

        system_prompt = (
            "You are a friendly and helpful general-purpose assistant. "
            "Your role is to answer user queries that do not fall into specialized categories. "
            "You will be given a user's intention and a description of the expected output. "
            "Based on this information, please provide a direct and clear response."
        )

        user_message = f"Task Description: {task.description}\n\nExpected Output Explanation: {task.expected_output}"

        # Build messages list with conversation history
        messages: list[AnyMessage] = [SystemMessage(content=system_prompt)]

        # Add conversation history for context
        # if dept_input.messages:
        #     # Add recent conversation messages for context
        #     messages.extend(dept_input.messages[-5:])  # Keep last 5 messages for context

        # Add current task message
        # messages.append(HumanMessage(content=user_message))

        # Call the LLM and get the response
        agent_response = await llm.ainvoke(messages)
        content = agent_response.content

        return str(content)

    except Exception as e:
        raise e


@node_error_handler(from_department=NodeNames_Dept.GENERAL_KNOWLEDGE)
async def general_knowledge_node(dept_input: DeptInput) -> Command:
    print_current_node(CURRENT_NODE_NAME)
    task = dept_input.task
    supervisor = dept_input.supervisor

    llm_response = await _call_general_knowledge_llm(dept_input)

    completed_task = CompletedTask(
        task_id=task.task_id,
        from_department=NodeNames_Dept.GENERAL_KNOWLEDGE,
        status=TaskStatus.SUCCESS,
        department_output=llm_response,
    )



    # Update only the operator-annotated fields to avoid concurrent key conflicts
    new_update = {
        "supervisor": {
            "completed_tasks": [completed_task],        # upsert_by_task_id will update/add by task_id
            "completed_task_ids": {task.task_id}        # operator.or_ will merge with existing
        }
    }

    return Command(
        update=new_update,
        goto=Command.PARENT
    )
