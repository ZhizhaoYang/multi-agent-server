from typing import Dict, Any
from datetime import datetime
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import AIMessage

from app.AI.core.llm import LLMFactory, LLMConfig, LLMProviders
from app.AI.supervisor_workflow.shared.models import ChatState
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_HQ
from app.AI.supervisor_workflow.shared.models.Chat import SupervisorStatus
from app.utils.logger import logger


llm = LLMFactory.create_llm(
    LLMConfig(
        provider=LLMProviders.DEEPSEEK.value,
        model="deepseek-reasoner",
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

    # Get original user query
    user_query = state.user_query

    # Get assessment summary if available
    assessment_summary = ""
    if state.assessment.assessment_summary:
        assessment_summary = f"\nASSESSMENT SUMMARY:\n{state.assessment.assessment_summary}\n"

    # Define newline for f-string compatibility
    newline = '\n'

    prompt = f"""You are an AI assistant that synthesizes results from multiple specialized departments to provide a comprehensive answer to the user's question.

ORIGINAL USER QUESTION:
{user_query}
{assessment_summary}
COMPLETED TASKS RESULTS:
{newline.join(completed_tasks_summary) if completed_tasks_summary else "No tasks were completed."}

CRITICAL INSTRUCTIONS:

1. CONTENT ANALYSIS: Carefully examine each department response. Some responses marked as "SUCCESS" might actually contain error messages (like "API key invalid", "rate limit exceeded", "service unavailable", etc.). Identify which responses are genuinely helpful vs. which contain error content.

2. SYNTHESIS APPROACH:
   - Use only genuinely successful responses to answer the user's question
   - If you detect error content in any response, acknowledge it briefly but don't let it dominate your answer
   - Integrate multiple successful responses logically
   - If all responses contain errors, be honest about the limitations while providing what value you can

3. RESPONSE QUALITY:
   - Address the user's original question directly and completely
   - Provide actionable insights based on successful results
   - Use a professional but conversational tone
   - Structure your response clearly with proper organization
   - If information is incomplete, be transparent but focus on what was successfully obtained

4. ERROR HANDLING:
   - Briefly mention if some departments encountered issues (without going into technical details)
   - Focus on the successful results and what they tell us about the user's question
   - Provide the best possible answer given the available successful information

Generate a final response that completely answers the user's question based on the genuinely successful task results:"""

    return prompt


async def call_llm_for_aggregation(llm, prompt: str) -> str:
    """
    Calls the LLM to generate the final aggregated response.
    """
    try:
        response = await llm.ainvoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        logger.error(f"LLM call failed in aggregator: {e}")
        # Fallback response if LLM fails
        return f"I apologize, but I encountered an error while generating the final response. However, I was able to process your request through multiple departments. Please try again or contact support if the issue persists."


async def aggregator_node(state: ChatState) -> Command:
    """
    Aggregator node that synthesizes all completed task results into a final response.

    This node:
    1. Collects all completed tasks and their results
    2. Gathers any errors that occurred
    3. Creates a comprehensive prompt for the LLM
    4. Generates a final synthesized response
    5. Updates the final_output and completes the workflow
    """

    logger.info(f"!! Aggregator node starting !!")
    logger.info(f"!! Completed tasks: {len(state.supervisor.completed_tasks)} !!")
    logger.info(f"!! Errors: {len(state.errors)} !!")

    new_updates: Dict[str, Any] = {}

    try:
        # Create the aggregation prompt
        prompt = create_aggregation_prompt(state)
        logger.info(f"!! Aggregation prompt created !!")

                # Call LLM for final response generation
        final_response = await call_llm_for_aggregation(llm, prompt)

        # Update the final output
        new_updates["final_output"] = final_response

        # Add the final response to messages
        new_updates["messages"] = [AIMessage(content=final_response)]

        # Update supervisor status to completed
        new_updates["supervisor"] = state.supervisor.model_copy(update={
            "supervisor_status": SupervisorStatus.COMPLETED
        })

        logger.info(f"!! Aggregation completed successfully !!")

        return Command(
            update=new_updates,
            goto=END
        )

    except Exception as e:
        logger.error(f"!! Aggregator node error: {e} !!")

        # Build error and fallback response
        new_error = state.build_error(e, CURRENT_NODE_NAME)

        fallback_response = "I apologize, but I encountered an error while generating the final response. Please try again."

        new_updates["final_output"] = fallback_response
        new_updates["errors"] = [new_error]
        new_updates["messages"] = [AIMessage(content=fallback_response)]
        new_updates["supervisor"] = state.supervisor.model_copy(update={
            "supervisor_status": SupervisorStatus.FAILED
        })

        return Command(
            update=new_updates,
            goto=END
        )
