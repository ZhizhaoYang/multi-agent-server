from enum import Enum, unique
from itertools import chain

class NodeNames(Enum):
    RESEARCHER = "researcher"
    MAP_SEARCHER = "mapSearcher"
    GENERAL_RESPONSE = "generalResponse"
    MATH_EXPERT = "mathExpert"

    AGGREGATOR = "aggregator"

    END = "END"
    START = "START"
    SUPERVISOR = "supervisor"