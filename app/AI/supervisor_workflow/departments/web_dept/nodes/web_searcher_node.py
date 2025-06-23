from langgraph.types import Command
from typing import Any, List, Optional
from langchain_core.messages import BaseMessage

from app.AI.supervisor_workflow.shared.models.Assessment import Task, CompletedTask, TaskStatus
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_Dept
from app.AI.supervisor_workflow.shared.models.Chat import SupervisorState
from app.AI.supervisor_workflow.departments.web_dept.agents.web_searcher_agent import create_web_searcher_agent
from app.AI.supervisor_workflow.departments.utils.errors import node_error_handler
from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput
from app.AI.supervisor_workflow.shared.utils.logUtils import print_current_node

CURRENT_NODE_NAME = NodeNames_Dept.WEB_DEPT.value

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
    Node that performs a web search based on the task description and expected output.
    Creates agent dynamically with bound prompt variables (clean, no state coupling).
    """
    print_current_node(CURRENT_NODE_NAME)

    task = dept_input.task
    supervisor = dept_input.supervisor

    llm_response = await _call_web_research_agent(task, dept_input.messages)

    final_message = llm_response.get("messages", [])[-1] if isinstance(llm_response,
                                                                       dict) and llm_response.get("messages") else llm_response
    completed_task = CompletedTask(
        task_id=task.task_id,
        from_department=NodeNames_Dept.WEB_DEPT,
        status=TaskStatus.SUCCESS,
        department_output=str(final_message.content) if isinstance(final_message, BaseMessage) else str(final_message)
    )

    return Command(
        update={
            "supervisor": {
                "completed_tasks": [completed_task],        # upsert_by_task_id will update/add by task_id
                "completed_task_ids": {task.task_id}        # operator.or_ will merge with existing
            }
        },
        goto=Command.PARENT
    )
