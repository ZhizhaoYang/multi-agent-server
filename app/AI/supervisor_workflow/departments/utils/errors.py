import functools
from datetime import datetime
from typing import Any, Callable, Coroutine
from langgraph.types import Command

from app.AI.supervisor_workflow.shared.models.Assessment import Task, CompletedTask, TaskStatus
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_Dept
from app.AI.supervisor_workflow.shared.models.Chat import ChatError, SupervisorState
from app.utils.logger import logger
from app.AI.supervisor_workflow.departments.web_dept.agents.web_searcher_agent import web_searcher_agent
from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput


def node_error_handler(from_department: NodeNames_Dept):
    """A decorator to handle exceptions in graph nodes, logging errors and returning a standard error response."""
    def decorator(func: Callable[[DeptInput], Coroutine[Any, Any, Any]]):
        @functools.wraps(func)
        async def wrapper(dept_input: DeptInput, *args, **kwargs) -> Any:
            try:
                return await func(dept_input, *args, **kwargs)
            except Exception as e:
                logger.error(f"!! Error in node {func.__name__} for department {from_department} !!: {e}", exc_info=True)

                new_error = ChatError(
                    node_name=func.__name__,
                    from_department=from_department,
                    error_message=str(e),
                    type=e.__class__.__name__,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )

                completed_task = CompletedTask(
                    task_id=dept_input.task.task_id,
                    from_department=from_department,
                    status=TaskStatus.ERROR,
                    department_output=f"An unexpected error occurred: {e}",
                )

                                                # Use operator annotations: operator.add for list, operator.or_ for set
                return Command(
                    update={
                        "supervisor": {
                            "completed_tasks": [completed_task],        # operator.add will append to existing list
                            "completed_task_ids": {dept_input.task.task_id}        # operator.or_ will union with existing set
                        },
                        "errors": [new_error]
                    },
                    goto=Command.PARENT
                )
        return wrapper
    return decorator
