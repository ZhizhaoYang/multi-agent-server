from IPython.display import display, Image
from langgraph.graph import StateGraph, START, END

from app.AI.workflows.models.chat_state import ChatWorkflowState
from app.AI.workflows.nodes.supervisor import supervisor_node
from app.AI.workflows.nodes.aggregator import aggregator_node
from app.AI.workflows.graph.worker_registry import WORKER_REGISTRY, NodeNames
from app.AI.workflows.constants import NodeNames
from app.AI.workflows.nodes.researcher import researcher_node
from app.AI.workflows.nodes.map_searcher import map_searcher_node
from app.AI.workflows.nodes.math_expert import math_expert_node
from app.AI.workflows.nodes.general_response import general_response_node

builder = StateGraph(ChatWorkflowState)

builder.add_node(
    NodeNames.SUPERVISOR.value,
    supervisor_node,
    destinations=(
        NodeNames.RESEARCHER.value,
        NodeNames.MAP_SEARCHER.value,
        NodeNames.MATH_EXPERT.value,
        NodeNames.GENERAL_RESPONSE.value
    ))

builder.add_node(NodeNames.AGGREGATOR.value, aggregator_node)
builder.add_node(NodeNames.RESEARCHER.value, researcher_node)
builder.add_node(NodeNames.MAP_SEARCHER.value, map_searcher_node)
builder.add_node(NodeNames.MATH_EXPERT.value, math_expert_node)
builder.add_node(NodeNames.GENERAL_RESPONSE.value, general_response_node)

builder.add_edge(START, NodeNames.SUPERVISOR.value)

builder.add_edge(NodeNames.RESEARCHER.value, NodeNames.SUPERVISOR.value)
builder.add_edge(NodeNames.MAP_SEARCHER.value, NodeNames.SUPERVISOR.value)
builder.add_edge(NodeNames.MATH_EXPERT.value, NodeNames.SUPERVISOR.value)

builder.add_edge(NodeNames.GENERAL_RESPONSE.value, END)
builder.add_edge(NodeNames.SUPERVISOR.value, NodeNames.AGGREGATOR.value)
builder.add_edge(NodeNames.AGGREGATOR.value, END)

# Compile and draw the graph after all nodes and edges are added
graph = builder.compile()
display(Image(graph.get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")))
# graph.get_graph(xray=False).draw_mermaid_png(output_file_path="graph.png")
