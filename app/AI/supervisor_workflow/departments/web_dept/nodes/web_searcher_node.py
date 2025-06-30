from langgraph.types import Command
from typing import Any, List, Optional
import asyncio
from langchain_core.messages import BaseMessage

from app.AI.supervisor_workflow.shared.models.Assessment import Task, CompletedTask, TaskStatus
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_Dept
from app.AI.supervisor_workflow.shared.models.Chat import SupervisorState
from app.AI.supervisor_workflow.departments.web_dept.agents.web_searcher_agent import create_web_searcher_agent
from app.AI.supervisor_workflow.departments.utils.errors import node_error_handler
from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput
from app.AI.supervisor_workflow.shared.utils.logUtils import print_current_node
from app.utils.logger import logger

CURRENT_NODE_NAME = NodeNames_Dept.WEB_DEPT.value


async def stream_web_search_response(response_text: str, department: str, publisher):
    """Stream the web search response character by character using queue-based system"""
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

            logger.info(f"Streamed web search response: {len(response_text)} characters total")
    except Exception as e:
        logger.error(f"Warning: Could not stream web search response: {e}")


async def _call_web_research_agent(task: Task, conversation_messages: Optional[List] = None) -> dict[str, Any]:
    """Creates a web searcher agent with bound prompt variables and calls it."""
    # Create agent with variables already bound in the prompt (no weird state coupling!)
    web_searcher_agent = create_web_searcher_agent(
        description=task.description,
        expected_output=task.expected_output
    )

    # Prepare messages with conversation history context
    messages = []
    if conversation_messages:
        # Add conversation history for context
        messages.extend(conversation_messages[-5:])  # Keep last 5 messages for context

    # Add current task message
    messages.append(("human", f"Please help me with: {task.description}"))

    # Call the agent with conversation context
    agent_response = await web_searcher_agent.ainvoke({
        "messages": messages
    })

    if not agent_response:
        raise ValueError("LLM call returned no response.")
    return agent_response

@node_error_handler(from_department=NodeNames_Dept.WEB_DEPT)
async def web_searcher_node(dept_input: DeptInput):
    """
    Web searcher node with real-time character-by-character streaming.
    Performs web search and streams results in real-time.
    """
    print_current_node(CURRENT_NODE_NAME)

    task = dept_input.task

    # Get publisher for streaming
    publisher = dept_input.get_stream_publisher()

    # Send initial signal
    initial_signal = "Searching the web..."
    logger.info("Streaming initial signal from Web Department")

    if publisher is not None:
        await publisher.publish_thought(
            content=initial_signal,
            source=NodeNames_Dept.WEB_DEPT.value,
            segment_id=1
        )
        await asyncio.sleep(0.01)

    # Perform web search
    llm_response = await _call_web_research_agent(task, dept_input.messages)

    # Extract final message content
    final_message = llm_response.get("messages", [])[-1] if isinstance(llm_response,
                                                                       dict) and llm_response.get("messages") else llm_response
    response_content = str(final_message.content) if isinstance(final_message, BaseMessage) else str(final_message)

    # Stream the search results character by character
    await stream_web_search_response(
        response_text=response_content,
        department="WebDepartment",
        publisher=publisher
    )

    completed_task = CompletedTask(
        task_id=task.task_id,
        from_department=NodeNames_Dept.WEB_DEPT,
        status=TaskStatus.SUCCESS,
        department_output=response_content
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
