from typing import Any
from langgraph.types import Command
from langchain_core.messages import BaseMessage

from app.AI.supervisor_workflow.shared.utils.logUtils import print_current_node
from app.AI.supervisor_workflow.shared.models.Assessment import Task, CompletedTask, TaskStatus
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_Dept
from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput
from app.AI.supervisor_workflow.departments.math_dept.agents.math_expert import create_math_expert_agent
from app.AI.supervisor_workflow.departments.utils.errors import node_error_handler

async def _call_math_expert_agent(task: Task) -> dict[str, Any]:
    """Creates a math expert agent with bound prompt variables and calls it."""
    # Create agent with variables already bound in the prompt (no weird state coupling!)
    math_expert_agent = create_math_expert_agent(
        description=task.description,
        expected_output=task.expected_output
    )

    # Call the agent with clean message-only state
    agent_response = await math_expert_agent.ainvoke({
        "messages": [("human", f"Please solve this math problem: {task.description}")]
    })

    if not agent_response:
        raise ValueError("LLM call returned no response.")
    return agent_response

@node_error_handler(from_department=NodeNames_Dept.MATH_DEPT)
async def math_dept_node(dept_input: DeptInput) -> Command:
    """
    Node that performs a math operation based on the task description and expected output.
    """
    print_current_node(NodeNames_Dept.MATH_DEPT.value)
    task = dept_input.task

    llm_response = await _call_math_expert_agent(task)

    final_message = llm_response.get("messages", [])[-1] if isinstance(llm_response,
                                                                       dict) and llm_response.get("messages") else llm_response

    completed_task = CompletedTask(
        task_id=task.task_id,
        from_department=NodeNames_Dept.MATH_DEPT,
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
