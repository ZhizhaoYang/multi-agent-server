from typing import Dict, Optional, List, Tuple, Iterator, Any
from langgraph.types import Command, Send
from langgraph.graph import END
from langchain_core.runnables import RunnableConfig
import asyncio
# Removed StreamWriter imports - now using queue-based streaming

from app.AI.supervisor_workflow.shared.models import ChatState
from app.AI.supervisor_workflow.shared.models.Assessment import LLMAssessmentOutput, Task
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_HQ, NodeNames_Dept
from app.utils.logger import logger
from app.AI.supervisor_workflow.shared.models.Chat import SupervisorStatus, SupervisorState
from app.AI.supervisor_workflow.departments.models.dept_input import DeptInput


CURRENT_NODE_NAME = NodeNames_HQ.SUPERVISOR.value

def _assessment_report_is_valid(assessment_report: Optional[LLMAssessmentOutput]) -> bool:
    return assessment_report is not None and \
        assessment_report.tasks is not None and \
        len(assessment_report.tasks) > 0 and \
        all(isinstance(task, Task) for task in assessment_report.tasks) and \
        all(isinstance(task.suggested_department, NodeNames_Dept) for task in assessment_report.tasks) and \
        assessment_report.assessment_summary is not None and \
        assessment_report.assessment_summary.strip() != ""


def _read_assessment_report(assessment_report: LLMAssessmentOutput) -> Tuple[bool, List[Task]]:
    """
    Reads and validates the tasks from the LLMAssessmentOutput.
    Returns a boolean indicating success and a list of sorted tasks.
    """
    if not _assessment_report_is_valid(assessment_report):
        logger.warning(
            f"Assessment report failed validation: {assessment_report.model_dump_json(indent=2) if assessment_report else 'None'}")
        return False, []

    try:
        tasks = assessment_report.tasks.copy()
        sorted_tasks = sorted(tasks, key=lambda task: task.priority)
        return True, sorted_tasks
    except Exception as e:
        logger.error(
            f"Unexpected error while sorting tasks in _read_assessment_report: {e}. Report: {assessment_report.model_dump_json(indent=2)}")
        return False, []


async def stream_task_dispatch(tasks: List[Task], publisher):
    """Stream the task dispatching information to the frontend"""
    try:
        if publisher is not None and tasks:
            # Send initial signal
            await publisher.publish_thought(
                content="Planning tasks...",
                source="Supervisor",
                segment_id=1
            )
            await asyncio.sleep(0.01)

            # Build the complete task list output
            task_lines = []
            for i, task in enumerate(tasks, 1):
                task_line = f"Task {i}: {task.description}"
                task_lines.append(task_line)

            # Combine all tasks into a single formatted output
            full_output = "\n".join(task_lines)

            # Stream the complete task list character by character
            for char_position, char in enumerate(full_output, 1):
                await publisher.publish_thought(
                    content=char,
                    source="Supervisor",
                    segment_id=char_position
                )
                await asyncio.sleep(0.01)

            # Send completion marker
            await publisher.publish_thought_complete(
                source="Supervisor",
                segment_id=len(full_output),
                total_length=len(full_output)
            )

            # logger.info(f"Streamed task dispatch: {len(tasks)} tasks, {len(full_output)} characters total")
    except Exception as e:
        logger.error(f"Warning: Could not stream task dispatch: {e}")


async def handle_task_dispatch(state: ChatState) -> Command:
    new_updates: Dict[str, Any] = {}

    # Check if assessment report exists (using new state composition)
    if state.assessment.assessment_report is None:
        logger.error(f"!! Assessment report is None !!")
        new_error = state.build_error(
            Exception("Assessment report does not exist"),
            CURRENT_NODE_NAME
        )

        new_updates["errors"] = [new_error]

        return Command(update=new_updates, goto=END)

    # Read and validate assessment report
    is_report_valid, tasks = _read_assessment_report(state.assessment.assessment_report)

    if not is_report_valid:
        new_error = state.build_error(
            Exception(f"Assessment report is invalid: {state.assessment.assessment_report}"),
            CURRENT_NODE_NAME
        )
        new_updates["errors"] = [new_error]

        return Command(update=new_updates, goto=END)

    # logger.info(f"!! Supervisor node handle_task_dispatch ---")

    # Get publisher and stream the tasks being dispatched
    publisher = state.get_stream_publisher()
    await stream_task_dispatch(tasks, publisher)

    new_updates["supervisor"] = SupervisorState(
        dispatched_tasks=tasks,
        dispatched_task_ids={task.task_id for task in tasks},
        supervisor_status=SupervisorStatus.PENDING
    )

    return Command(
        update=new_updates,
        graph=CURRENT_NODE_NAME,
        goto=[Send(task.suggested_department.value, DeptInput(
            task=task,
            supervisor=new_updates["supervisor"],
            messages=state.messages,  # Pass conversation history
            thread_id=getattr(state, 'thread_id', ''),  # Pass thread context
            user_query=state.user_query,  # Pass current user query
            stream_queue_id=state.stream_queue_id  # Pass queue ID for streaming
        )) for task in tasks],
    )


def handle_task_completion(state: ChatState) -> Command | None:
    new_updates: Dict[str, Any] = {}

    logger.info(f"!! Supervisor node handle_task_completion ---")

    # check if supervisor is pending, if pending, just return None, keep waiting
    if state.supervisor.supervisor_status != SupervisorStatus.PENDING:
        return None

    # check if all tasks are completed, else return None, keep waiting
    if state.supervisor.dispatched_task_ids - state.supervisor.completed_task_ids != set():
        return None

    # Update supervisor state to mark completion phase
    new_updates["supervisor"] = state.supervisor.model_copy(update={
        "supervisor_status": SupervisorStatus.COMPLETED
    })
    # Route to aggregator node instead of END
    return Command(
        update=new_updates,
        goto=NodeNames_HQ.AGGREGATOR.value
    )


async def supervisor_node(state: ChatState) -> Iterator[Send | Command] | Command | None:
    """
    Enhanced supervisor node with state composition pattern and streaming.

    Manages dispatching tasks to department nodes based on assessment_report,
    streams task information to frontend, and waits for completion before routing to aggregator.
    """
    # Handle different supervisor states
    match state.supervisor.supervisor_status:
        case SupervisorStatus.IDLE:
            return await handle_task_dispatch(state)

        case SupervisorStatus.PENDING:
            return handle_task_completion(state)

        case SupervisorStatus.COMPLETED:
            new_updates = state.model_copy(update={
                "supervisor": SupervisorState(
                    supervisor_status=SupervisorStatus.IDLE,
                    dispatched_tasks=[],
                    dispatched_task_ids=set(),
                    completed_tasks=[],
                    completed_task_ids=set()
                )
            })

            return Command(update=new_updates, goto=NodeNames_HQ.SUPERVISOR.value)

        case _:
            logger.info(f"!! Supervisor in unknown state: {state.supervisor.supervisor_status} !!")
            return None
