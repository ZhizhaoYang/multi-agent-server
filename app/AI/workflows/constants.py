from enum import Enum, unique
from itertools import chain

class NodeNames(Enum):
    RESEARCHER = "researcher"
    MAP_SEARCHER = "mapSearcher"
    GENERAL_RESPONSE = "generalResponse"
    SUPERVISOR = "supervisor"
    SUMMARY = "summary"

    END = "END"
    START = "START"