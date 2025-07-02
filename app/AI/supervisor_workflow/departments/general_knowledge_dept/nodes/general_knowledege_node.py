from langgraph.types import Command
import asyncio

from langchain_core.messages import SystemMessage, AnyMessage

from app.AI.supervisor_workflow.shared.models import CompletedTask, TaskStatus, NodeNames_Dept
from app.AI.core.llm import LLMFactory, LLMConfig, LLMProviders
from app.AI.supervisor_workflow.shared.utils.logUtils import print_current_node
from app.AI.supervisor_workflow.departments.utils.errors import node_error_handler
from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput
from app.utils.logger import logger

CURRENT_NODE_NAME = NodeNames_Dept.GENERAL_KNOWLEDGE.value


async def stream_knowledge_response(response_text: str, department: str, publisher):
    """Stream the knowledge response character by character using queue-based system"""
    try:
        if publisher is not None:
            # Stream each character with segment_id as character position
            for char_position, char in enumerate(response_text, 1):
                await publisher.publish_thought(
                    content=char,
                    source=department,
                    segment_id=char_position
                )
                await asyncio.sleep(0.01)  # Small delay between characters

            # Send completion marker
            await publisher.publish_thought_complete(
                source=department,
                segment_id=len(response_text),
                total_length=len(response_text)
            )

            logger.info(f"Streamed knowledge response: {len(response_text)} characters total")
    except Exception as e:
        logger.error(f"Warning: Could not stream knowledge response: {e}")


@node_error_handler(from_department=NodeNames_Dept.GENERAL_KNOWLEDGE)
async def _call_general_knowledge_llm(dept_input: DeptInput) -> str:
    """Call the LLM and return the response content as a string"""
    task = dept_input.task

    try:
        llm = LLMFactory.create_llm(
            LLMConfig(
                provider=LLMProviders.OPENAI.value,
                model="gpt-4.1-nano",
                temperature=1.0,
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
    """
    General knowledge department with real-time character-by-character streaming.
    """
    print_current_node(CURRENT_NODE_NAME)
    task = dept_input.task

    # Get publisher for streaming
    publisher = dept_input.get_stream_publisher()

    # Send initial signal
    initial_signal = "Processing your query..."
    logger.info("Streaming initial signal from General Knowledge Department")

    if publisher is not None:
        await publisher.publish_thought(
            content=initial_signal,
            source=NodeNames_Dept.GENERAL_KNOWLEDGE.value,
            segment_id=1
        )
        await asyncio.sleep(0.01)

    # Get LLM response
    llm_response = await _call_general_knowledge_llm(dept_input)

    # Stream the response character by character
    await stream_knowledge_response(
        response_text=llm_response,
        department=NodeNames_Dept.GENERAL_KNOWLEDGE.value,
        publisher=publisher
    )

    completed_task = CompletedTask(
        task_id=task.task_id,
        from_department=NodeNames_Dept.GENERAL_KNOWLEDGE,
        status=TaskStatus.SUCCESS,
        department_output=llm_response,
    )

    # Return result to supervisor
    return Command(
        update={
            "supervisor": {
                "completed_tasks": [completed_task],
                "completed_task_ids": {task.task_id}
            }
        },
        goto=Command.PARENT
    )
