from langgraph.graph import StateGraph, START
from enum import Enum

from app.AI.workflows.models.chat_state import ChatState
from app.AI.workflows.nodes.supervisor import supervisor_node
from app.AI.workflows.nodes.researcher import researcher_node
from app.AI.workflows.nodes.map_searcher import map_searcher_node
from app.AI.workflows.constants import NodeNames
from app.AI.workflows.nodes.general_response import general_response_node

class Nodes(Enum):
    """langgraph Nodes"""

    RESEARCHER = "researcher"
    MAP_SEARCHER = "mapSearcher"
    GENERAL_RESPONSE = "generalResponse"
    FINISH = "FINISH"
    SUPERVISOR = "supervisor"

builder = StateGraph(ChatState)

builder.add_node(NodeNames.SUPERVISOR.value, supervisor_node)
builder.add_node(NodeNames.RESEARCHER.value, researcher_node)
builder.add_node(NodeNames.MAP_SEARCHER.value, map_searcher_node)
builder.add_node(NodeNames.GENERAL_RESPONSE.value, general_response_node)

builder.add_edge(START, NodeNames.SUPERVISOR.value)

graph = builder.compile()

# graph.get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")