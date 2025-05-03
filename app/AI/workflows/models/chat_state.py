from langgraph.graph import MessagesState
from typing import List
from typing import Annotated
import operator

class ChatState(MessagesState):
    query: str
    nodes_history: Annotated[List[str], operator.add]
    nodes_count: Annotated[int, operator.add]
