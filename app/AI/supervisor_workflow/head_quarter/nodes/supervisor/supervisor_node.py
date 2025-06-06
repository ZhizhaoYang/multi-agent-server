from typing import Dict, Optional, List, Tuple, Iterator
from datetime import datetime
from langgraph.types import Command, Send
from langgraph.graph import END

from app.AI.supervisor_workflow.shared.models import ChatState, ChatError
from app.AI.supervisor_workflow.shared.models.Assessment import LLMAssessmentOutput, Task
from app.AI.supervisor_workflow.shared.models.Nodes import NodeNames_HQ, NodeNames_Dept
from app.utils.logger import logger


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
        logger.warning(f"Assessment report failed validation: {assessment_report.model_dump_json(indent=2) if assessment_report else 'None'}")
        return False, []

    # If _assessment_report_is_valid has passed, we know:
    # - assessment_report.tasks is a non-empty list.
    # - Each item in assessment_report.tasks is an instance of Task.
    # - Each Task instance has a 'priority' attribute which is an int > 0.
    # Therefore, direct sorting should be safe.
    try:
        # assessment_report.tasks directly gives List[Task]
        # Pydantic would have already validated 'priority' as an int during LLMAssessmentOutput parsing.
        tasks = assessment_report.tasks.copy()
        sorted_tasks = sorted(tasks, key=lambda task: task.priority)
        return True, sorted_tasks
    except Exception as e:
        # This is a fallback for truly unexpected issues during sorting,
        # e.g., if a malformed Task object somehow bypassed Pydantic validation,
        # or if an unexpected exception occurs within the sort itself.
        logger.error(f"Unexpected error while sorting tasks in _read_assessment_report: {e}. Report: {assessment_report.model_dump_json(indent=2)}")
        return False, []


def supervisor_node(state: ChatState) -> Iterator[Send | Command] | Command:
    """
    Manages dispatching tasks to department nodes based on assessment_report
    and waits for their completion before proceeding.
    """
    logger.info(f"!! Supervisor node state: {state} !!")
    new_updates: Dict = {}

    try:
        # report does not exist
        if state.assessment_report is None:
            print(f"!! Assessment report is None !!")
            new_updates["errors"] = [
                ChatError(
                    node_name=CURRENT_NODE_NAME,
                    error=f"Assessment report is invalid: {state.assessment_report}",
                    type="invalid_assessment_report",
                    timestamp=datetime.now().isoformat()
                )
            ]
            return Command(update=new_updates, goto=END)

        is_report_valid, tasks = _read_assessment_report(state.assessment_report)
        if not is_report_valid:
            print(f"!! Assessment report is invalid !!")
            new_updates["errors"] = [
                ChatError(
                    node_name=CURRENT_NODE_NAME,
                    error=f"Assessment report is invalid: {state.assessment_report}",
                    type="invalid_assessment_report",
                    timestamp=datetime.now().isoformat()
                )
            ]
            return Command(update=new_updates, goto=END)

        new_updates["dispatched_tasks"] = tasks
        logger.info(f"!! dispatched_tasks: {type(tasks)} \n{tasks} !!")

        return Command(
            update=new_updates,
            goto=[Send(task.suggested_department.value, task) for task in tasks]
        )

    except Exception as e:
        print(f"!! Supervisor node Exception: {e} !!")
        new_updates["errors"] = [state.build_error(e, CURRENT_NODE_NAME)]
        return Command(update=new_updates, goto=END)
