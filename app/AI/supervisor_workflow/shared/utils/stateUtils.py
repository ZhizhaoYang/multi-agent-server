from typing import Annotated
from pydantic import BaseModel
from operator import add, or_


def upsert_by_task_id(left_list, right_list):
    """
    Custom operator for completed_tasks: upsert behavior based on task_id.
    - If task_id exists in left_list, update it with the version from right_list
    - If task_id doesn't exist, add it to the list

    Args:
        left_list: Existing list of CompletedTask objects
        right_list: New list of CompletedTask objects to merge

    Returns:
        Merged list with upserted tasks
    """
    if not left_list:
        left_list = []
    if not right_list:
        right_list = []

    # Create a copy of the left list to modify
    result = list(left_list)

    # Create a mapping of existing task_ids for quick lookup
    existing_task_ids = {task.task_id: idx for idx, task in enumerate(result)}

    # Process each task from the right list
    for new_task in right_list:
        if new_task.task_id in existing_task_ids:
            # Update existing task
            idx = existing_task_ids[new_task.task_id]
            result[idx] = new_task
        else:
            # Add new task
            result.append(new_task)
            existing_task_ids[new_task.task_id] = len(result) - 1

    return result

# Generic reducer factory for any Pydantic model with operator-annotated fields
def create_state_merger(model_class):
    """
    Creates a generic merger function for any Pydantic model.
    Automatically handles operator-annotated fields for LangGraph concurrent updates.

    Usage:
        merge_supervisor_states = create_state_merger(SupervisorState)
        merge_assessment_states = create_state_merger(AssessmentState)

    Then use in Annotated types:
        supervisor: Annotated[SupervisorState, merge_supervisor_states]
    """

    def merge_states(left, right):
        """Generic state merger for concurrent updates"""

        def get_field_value(obj, field_name):
            """Get field value from either object or dict"""
            if isinstance(obj, dict):
                return obj.get(field_name)
            return getattr(obj, field_name, None)

        def merge_field(field_name, field_info, left_val, right_val):
            """Merge field values based on operator annotations"""
            # Check for operator annotations
            if hasattr(field_info, 'metadata') and field_info.metadata:
                for annotation in field_info.metadata:
                    if annotation == add:
                        # List concatenation: left + right
                        left_list = left_val if left_val is not None else []
                        right_list = right_val if right_val is not None else []
                        return left_list + right_list
                    elif annotation == or_:
                        # Set union: left | right
                        left_set = left_val if left_val is not None else set()
                        right_set = right_val if right_val is not None else set()
                        return left_set | right_set
                    elif annotation == upsert_by_task_id:
                        # Custom upsert behavior for task lists
                        left_list = left_val if left_val is not None else []
                        right_list = right_val if right_val is not None else []
                        return upsert_by_task_id(left_list, right_list)

            # No operator annotation - right wins (latest update)
            return right_val if right_val is not None else left_val

        # Build merged data for the model
        merged_data = {}

        # Process each field in the model
        for field_name, field_info in model_class.model_fields.items():
            left_val = get_field_value(left, field_name)
            right_val = get_field_value(right, field_name)

            # Skip fields not provided in partial updates (dicts)
            if isinstance(right, dict) and field_name not in right:
                merged_data[field_name] = left_val
            else:
                merged_data[field_name] = merge_field(field_name, field_info, left_val, right_val)

        # Create new instance with merged data
        return model_class(**{k: v for k, v in merged_data.items() if v is not None})

    return merge_states

