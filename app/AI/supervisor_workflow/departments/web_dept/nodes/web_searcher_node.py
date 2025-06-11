from langgraph.types import Command
from typing import Any
from langchain_core.messages import BaseMessage

from app.AI.supervisor_workflow.shared.models.Assessment import Task, CompletedTask, TaskStatus
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_Dept
from app.AI.supervisor_workflow.shared.models.Chat import SupervisorState
from app.AI.supervisor_workflow.departments.web_dept.agents.web_searcher_agent import web_searcher_agent
from app.AI.supervisor_workflow.departments.utils.errors import node_error_handler
from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput
from app.AI.supervisor_workflow.shared.utils.logUtils import print_current_node

CURRENT_NODE_NAME = NodeNames_Dept.WEB_DEPT.value

async def _call_web_research_agent(task: Task) -> dict[str, Any]:
    """Calls the web searcher agent and returns the response, raising an error if the response is empty."""
    agent_response = await web_searcher_agent.ainvoke({"description": task.description, "expected_output": task.expected_output})
    if not agent_response:
        raise ValueError("LLM call returned no response.")
    return agent_response

@node_error_handler(from_department=NodeNames_Dept.WEB_DEPT)
async def web_searcher_node(dept_input: DeptInput):
    """
    Node that performs a web search based on the task description and expected output.
    """
    print_current_node(CURRENT_NODE_NAME)

    task = dept_input.task
    supervisor = dept_input.supervisor

    llm_response = await _call_web_research_agent(task)

    final_message = llm_response.get("messages", [])[-1] if isinstance(llm_response,
                                                                       dict) and llm_response.get("messages") else llm_response
    completed_task = CompletedTask(
        task_id=task.task_id,
        from_department=NodeNames_Dept.WEB_DEPT,
        status=TaskStatus.SUCCESS,
        department_output=str(final_message.content) if isinstance(final_message, BaseMessage) else str(final_message)
    )

            # Use operator annotations: operator.add for list, operator.or_ for set
    return Command(
        update={
            "supervisor": {
                "completed_tasks": [completed_task],        # operator.add will append to existing list
                "completed_task_ids": {task.task_id}        # operator.or_ will union with existing set
            }
        },
        goto=Command.PARENT
    )
