from pydantic import BaseModel, Field
from dataclasses import dataclass
from typing import Dict, Optional, List
from langchain_core.runnables.base import Runnable

from app.AI.supervisor_workflow.shared.models import NodeNames_Dept
from app.AI.supervisor_workflow.departments import math_dept_subgraph, web_dept_subgraph, general_knowledge_subgraph

@dataclass
class Dept_Info:
    department_name: str = Field(..., description="The unique name identifying the department.")
    description: str = Field(...,
                             description="A concise summary of the department's primary functions and areas of expertise.")
    is_available: bool = Field(default=True, description="Whether the department is currently available for use.")
    node_func: Runnable = Field(..., description="The department's node function that will be used to process the task.")

    # model_config = {
    #     "arbitrary_types_allowed": True
    # }


_INITIAL_REGISTERED_DEPARTMENTS: Dict[str, Dept_Info] = {
    NodeNames_Dept.WEB_DEPT.value: Dept_Info(
        department_name=NodeNames_Dept.WEB_DEPT.value,
        description="Manages web interactions, including browsing, online data retrieval, and internet-based research, some up-to-date information is required.",
        node_func=web_dept_subgraph
    ),
    NodeNames_Dept.MATH_DEPT.value: Dept_Info(
        department_name=NodeNames_Dept.MATH_DEPT.value,
        description="Specializes in mathematical computations, algebraic problem-solving, and quantitative analysis.",
        node_func=math_dept_subgraph
    ),
    NodeNames_Dept.GENERAL_KNOWLEDGE.value: Dept_Info(
        department_name=NodeNames_Dept.GENERAL_KNOWLEDGE.value,
        description="When the user's query is not related to the specific domain of the other departments, this department will be used to answer the question. It probably will query a Large Language Model directly to answer the question.",
        node_func=general_knowledge_subgraph
    )
}


class DepartmentRegistry(BaseModel):
    oncall_departments: Dict[str, Dept_Info] = Field(
        description="A dictionary of all currently registered and operational departments, keyed by department name."
    )

    model_config = { "arbitrary_types_allowed": True } # for PydanticSchemaGenerationError, the node_func field is not allowed to be a Runnable

    def register_department(self, department_info: Dept_Info):
        """Registers a new department or updates an existing one if the name matches."""
        self.oncall_departments[department_info.department_name] = department_info

    def get_department(self, department_name: str) -> Optional[Dept_Info]:
        """Retrieves a department by its name. Returns None if not found."""
        return self.oncall_departments.get(department_name)

    def get_all_departments(self) -> Dict[str, Dept_Info]:
        """Returns a copy of all registered departments to prevent direct modification."""
        return self.oncall_departments.copy()

    def get_all_available_departments(self) -> Dict[str, Dept_Info]:
        """Returns a copy of all registered departments to prevent direct modification."""
        return {
            department_name: department_info
            for department_name, department_info in self.oncall_departments.items()
            if department_info.is_available
        }

    def get_available_department_names(self) -> List[str]:
        """Returns a list of names of all available departments."""
        return [department_name for department_name, department_info in self.oncall_departments.items() if department_info.is_available]

    def get_available_department_names_string(self, seperator: str = ",") -> str:
        """Returns a string of names of all available departments."""
        return seperator.join(self.get_available_department_names())

    def get_available_departments_func_map(self) -> Dict[str, Runnable]:
        """Returns a dictionary of names of all available departments and their corresponding functions."""
        return {
            department_name: department_info.node_func
            for department_name, department_info in self.oncall_departments.items()
            if department_info.is_available
        }


department_registry = DepartmentRegistry(oncall_departments=_INITIAL_REGISTERED_DEPARTMENTS.copy())
