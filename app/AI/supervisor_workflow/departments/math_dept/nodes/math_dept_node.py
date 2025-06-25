from typing import Any, List
import json
import asyncio
from langgraph.types import Command
from langchain_core.messages import BaseMessage, AnyMessage, HumanMessage
from langgraph.config import get_stream_writer

from app.AI.supervisor_workflow.shared.utils.logUtils import print_current_node
from app.AI.supervisor_workflow.shared.models.Assessment import Task, CompletedTask, TaskStatus
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_Dept
from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput
from app.AI.supervisor_workflow.departments.math_dept.agents.math_expert import create_math_expert_agent
from app.AI.supervisor_workflow.departments.utils.errors import node_error_handler
from app.utils.logger import logger

# Define the exact order for concatenating thoughts
MATH_THOUGHT_ORDER = [
    "understanding",   # What the problem is about
    "analysis",        # Breaking down components
    "approach",        # Strategy to solve
    "working",         # Step-by-step calculations
    "verification"     # Checking the work
]

def concatenate_thoughts_with_markers(thoughts: dict) -> str:
    """
    Concatenate all thought sections into one text with markers

    Args:
        thoughts: Dictionary of thought sections from JSON response

    Returns:
        Single concatenated string with markers
    """
    concatenated_parts = []

    for section_type in MATH_THOUGHT_ORDER:
        if section_type in thoughts and thoughts[section_type]:
            marker = section_type.upper()
            content = thoughts[section_type]
            concatenated_parts.append(f"{marker}: {content}")

    return "\n\n".join(concatenated_parts)

async def stream_concatenated_thoughts(full_text: str, department: str):
    """Stream the full concatenated thought text character by character with position-based segment_id"""
    try:
        writer = get_stream_writer()
        if writer is not None:
            # Stream each character with segment_id as character position
            for char_position, char in enumerate(full_text, 1):
                writer({
                    "thought_content": char,
                    "type": "thought",
                    "source": department,
                    "segment_id": char_position  # Character position in the full text
                })
                await asyncio.sleep(0.01)  # Small delay between characters

            # Send completion marker
            writer({
                "thought_content": "",
                "type": "thought_complete",
                "source": department,
                "segment_id": len(full_text),  # Total character count
                "total_length": len(full_text)
            })

            logger.info(f"Streamed concatenated thoughts: {len(full_text)} characters total")
    except Exception as e:
        logger.error(f"Warning: Could not stream concatenated thoughts: {e}")

def extract_json_from_response(text: str) -> dict:
    """
    Extract JSON from LLM response, handling various formats and cleaning up text.

    Args:
        text: Raw text from LLM that should contain JSON

    Returns:
        Parsed JSON dictionary

    Raises:
        ValueError: If no valid JSON is found
    """
    # Remove code blocks if present
    text = text.replace("```json", "").replace("```", "").strip()

    # Try to find JSON content between braces
    start_brace = text.find('{')
    end_brace = text.rfind('}')

    if start_brace == -1 or end_brace == -1:
        raise ValueError("No JSON braces found in response")

    json_text = text[start_brace:end_brace + 1]

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        logger.error(f"JSON text: {json_text}")
        raise ValueError(f"Invalid JSON format: {e}")

async def _call_math_expert_agent_fallback(task: Task, conversation_messages: List[AnyMessage] = []) -> dict[str, Any]:
    """Fallback method for simple math problems without JSON structure"""
    math_expert_agent = create_math_expert_agent()

    messages = []
    if conversation_messages:
        messages.extend(conversation_messages[-5:])

    messages.append(HumanMessage(f"Please solve this math problem step by step: {task.description}"))

    agent_response = await math_expert_agent.ainvoke({"messages": messages})

    if not agent_response:
        raise ValueError("LLM call returned no response.")
    return agent_response

@node_error_handler(from_department=NodeNames_Dept.MATH_DEPT)
async def math_dept_node(dept_input: DeptInput) -> Command:
    """
    Math department with JSON structured output and concatenated character-by-character streaming
    """
    print_current_node(NodeNames_Dept.MATH_DEPT.value)
    task = dept_input.task

    # Create clean math problem prompt for JSON output
    math_prompt = f"""Please solve this math problem and provide your response in the required JSON format.

Problem: {task.description}
Context: {dept_input.user_query}
Expected Output: {task.expected_output}

Remember to use the calculator tool for all numerical computations and provide your response as valid JSON."""

    # Get clean math expert agent
    math_expert_agent = create_math_expert_agent()

    # Prepare messages with conversation history
    messages = []
    if dept_input.messages:
        messages.extend(dept_input.messages[-5:])
    messages.append(HumanMessage(content=math_prompt))

    final_result = ""

    try:
        logger.info("Starting JSON-based math processing...")

        # Get full response from math agent
        response = await math_expert_agent.ainvoke({"messages": messages})

        if not response or not response.get("messages"):
            raise ValueError("No response from math expert agent")

        full_content = response["messages"][-1].content
        logger.info(f"Raw response length: {len(full_content)} characters")

        # Parse JSON from response
        try:
            json_response = extract_json_from_response(full_content)
            logger.info("Successfully parsed JSON response")

            # Extract result and thoughts
            final_result = json_response.get("result", "").strip()
            thoughts = json_response.get("thoughts", {})

            if not final_result:
                logger.warning("No result found in JSON, using full content")
                final_result = full_content

            # Concatenate all thoughts with markers
            if thoughts:
                concatenated_thoughts = concatenate_thoughts_with_markers(thoughts)
                logger.info(f"Concatenated thoughts length: {len(concatenated_thoughts)} characters")

                # Stream the concatenated text character by character
                await stream_concatenated_thoughts(
                    full_text=concatenated_thoughts,
                    department="MathDepartment"
                )
            else:
                logger.warning("No thoughts found in JSON response")

            logger.info(f"Final result: {final_result}")

        except ValueError as json_error:
            logger.error(f"JSON parsing failed: {json_error}")
            logger.info("Falling back to text-based processing...")

            # Fallback: treat as plain text result
            final_result = full_content

            # Stream as fallback text
            fallback_text = f"REASONING: {full_content}"
            await stream_concatenated_thoughts(
                full_text=fallback_text,
                department="MathDepartment"
            )

    except Exception as e:
        logger.error(f"Error in math processing: {e}")

        # Stream error message
        error_text = f"ERROR: {str(e)}"
        await stream_concatenated_thoughts(
            full_text=error_text,
            department="MathDepartment"
        )

        # Fallback to simple method
        try:
            logger.info("Using fallback math agent...")
            llm_response = await _call_math_expert_agent_fallback(task, dept_input.messages)
            final_message = llm_response.get("messages", [])[-1] if isinstance(llm_response, dict) and llm_response.get("messages") else llm_response
            final_result = str(final_message.content) if isinstance(final_message, BaseMessage) else str(final_message)
        except Exception as fallback_error:
            final_result = f"Error in math calculation: {str(fallback_error)}"

    # Return result to supervisor
    completed_task = CompletedTask(
        task_id=task.task_id,
        from_department=NodeNames_Dept.MATH_DEPT,
        status=TaskStatus.SUCCESS,
        department_output=final_result
    )

    return Command(
        update={
            "supervisor": {
                "completed_tasks": [completed_task],
                "completed_task_ids": {task.task_id}
            }
        },
        goto=Command.PARENT
    )
