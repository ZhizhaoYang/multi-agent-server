from enum import Enum, unique


@unique
class NodeNames_Dept(Enum):
    WEB_DEPT = "WebDepartment"
    MATH_DEPT = "MathDepartment"
    DOCUMENTATION = "Documentation"
    MATH_EXPERT = "MathExpert"
    NEWS = "News"
    GENERAL_KNOWLEDGE = "GeneralKnowledge"


@unique
class NodeNames_HQ(Enum):
    INITIALIZER = "Initializer"
    SUPERVISOR = "Supervisor"
    ASSESSMENT = "Assessment"
    AGGREGATOR = "Aggregator"
    FINAL_RESPONSE = "FinalResponse"





