from typing import Dict, Any
from langgraph.types import Command
from langchain_core.messages import AIMessage
import uuid
import asyncio
from langchain_core.language_models import BaseChatModel

from app.AI.core.llm import LLMFactory, LLMConfig, LLMProviders
from app.AI.supervisor_workflow.shared.models import ChatState
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_HQ
from app.AI.supervisor_workflow.shared.models.Chat import SupervisorStatus
from app.utils.logger import logger
from app.AI.supervisor_workflow.shared.models.stream_models import StreamPublisher


llm = LLMFactory.create_llm(
    LLMConfig(
        provider=LLMProviders.OPENAI.value,
        model="gpt-4.1-mini",
        temperature=1.0,
    )
)
CURRENT_NODE_NAME = NodeNames_HQ.AGGREGATOR.value


def create_aggregation_prompt(state: ChatState) -> str:
    """
    Creates a comprehensive prompt for the LLM to generate the final response.
    Focuses on completed tasks and lets the LLM detect error content in responses.
    """

    # Gather completed tasks information
    completed_tasks_summary = []
    if state.supervisor.completed_tasks:
        for completed_task in state.supervisor.completed_tasks:
            # Try to find original task description from dispatched tasks
            original_task = None
            for dispatched_task in state.supervisor.dispatched_tasks:
                if dispatched_task.task_id == completed_task.task_id:
                    original_task = dispatched_task
                    break

            task_description = original_task.description if original_task else f"Task ID: {completed_task.task_id}"
            expected_output = original_task.expected_output if original_task else "Not specified"

            task_info = f"""
Task: {task_description}
Expected Output: {expected_output}
Department: {completed_task.from_department.value}
Status: {completed_task.status.value}
Department Response: {completed_task.department_output if completed_task.department_output else 'No response provided'}
"""
    completed_tasks_summary.append(task_info.strip())

    user_query = state.user_query
    newline = '\n'

    prompt = f"""You are a helpful AI assistant. The user asked you a question and you have gathered the necessary information to respond.

USER'S QUESTION:
{user_query}

AVAILABLE INFORMATION:
{newline.join(completed_tasks_summary) if completed_tasks_summary else "No additional information available."}

INSTRUCTIONS:
1. Respond directly and naturally to the user's question as if you are a single AI assistant
2. Use the available information to provide a helpful answer
3. DO NOT mention any internal processes, tasks, departments, or technical details
4. DO NOT reference "completing tasks" or "processing" or "synthesis"
5. If the information contains obvious error messages (like API errors), ignore those parts
6. For simple questions like greetings, respond naturally without over-explaining
7. Make your response feel conversational and human-like
8. Focus only on what the user actually wants to know

Provide a direct, natural response to the user:"""

    return prompt


async def call_llm_for_aggregation(llm: BaseChatModel, prompt: str, publisher: StreamPublisher, state: ChatState) -> str:
    """
    Calls the LLM to generate the final aggregated response with simple streaming.
    Only sends initial signal and completion marker.
    """
    try:
        # Send initial signal
        initial_signal = "Finalizing response..."
        logger.info("Streaming initial signal from Aggregator")

        if publisher is not None:
            await publisher.publish_thought(
                content=initial_signal,
                source=NodeNames_HQ.AGGREGATOR.value,
                segment_id=1
            )

        # Get the full response
        full_response = ""
        async for chunk in llm.astream(prompt):
            if hasattr(chunk, 'content') and chunk.content:
                chunk_text = str(chunk.content) if chunk.content else ""
                full_response += chunk_text

        # Send completion marker after successful generation
        if publisher is not None:
            await publisher.publish_thought_complete(
                source=NodeNames_HQ.AGGREGATOR.value,
                segment_id=1,
                total_length=len(full_response),
                content="Done"
            )
            logger.info(f"Aggregator completed successfully: {len(full_response)} characters generated")

        return full_response
    except Exception as e:
        logger.error(f"LLM call failed in aggregator: {e}")
        # Fallback response if LLM fails
        fallback_response = f"I apologize, but I encountered an error while generating the final response. However, I was able to process your request through multiple departments. Please try again or contact support if the issue persists."

        # Send completion marker for fallback response too
        if publisher is not None:
            await publisher.publish_thought_complete(
                source=NodeNames_HQ.AGGREGATOR.value,
                segment_id=1,
                total_length=len(fallback_response)
            )

        return fallback_response


async def aggregator_node(state: ChatState) -> Command:
    """
    Aggregator node that synthesizes all completed task results into a final response.

    This node:
    1. Collects all completed tasks and their results
    2. Gathers any errors that occurred
    3. Creates a comprehensive prompt for the LLM
    4. Generates a final synthesized response with simple streaming (initial + completion)
    5. Updates the final_output and completes the workflow
    """

    logger.info(f"!! Aggregator node starting !!")
    logger.info(f"!! Completed tasks: {len(state.supervisor.completed_tasks)} !!")
    logger.info(f"!! Errors: {len(state.errors)} !!")

    new_updates: Dict[str, Any] = {}

    # Get publisher for streaming
    publisher = state.get_stream_publisher()

    try:
        # Create the aggregation prompt
        prompt = create_aggregation_prompt(state)
        # logger.info(f"!! Aggregation prompt created !!")

        # Call LLM for final response generation with simple streaming
        final_response = await call_llm_for_aggregation(llm, prompt, publisher, state)

        # Update the final output
        new_updates["final_output"] = final_response

        # Add the final response to messages
        new_updates["messages"] = [AIMessage(content=final_response, id=str(uuid.uuid4()))]

        # logger.info(f"!! Aggregation completed successfully !!")

        return Command(
            update=new_updates,
            goto=NodeNames_HQ.FINAL_RESPONSE.value
        )

    except Exception as e:
        logger.error(f"!! Aggregator node error: {e} !!")

        # Build error and fallback response
        new_error = state.build_error(e, CURRENT_NODE_NAME)

        fallback_response = "I apologize, but I encountered an error while generating the final response. Please try again."

        # Send completion marker for error case
        if publisher:
            await publisher.publish_thought_complete(
                source=NodeNames_HQ.AGGREGATOR.value,
                segment_id=1,
                total_length=len(fallback_response)
            )

        new_updates["final_output"] = fallback_response
        new_updates["errors"] = [new_error]
        new_updates["messages"] = [AIMessage(content=fallback_response, id=str(uuid.uuid4()))]

        return Command(
            update=new_updates,
            goto=NodeNames_HQ.FINAL_RESPONSE.value
        )
