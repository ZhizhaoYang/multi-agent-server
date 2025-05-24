from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum

from app.AI.workflows.models.chat_state import ChatWorkflowState
# from app.AI.workflows.nodes.supervisor import supervisor_node
from app.AI.workflows.nodes.researcher import researcher_node
from app.AI.workflows.nodes.map_searcher import map_searcher_node
from app.AI.workflows.nodes.general_response import general_response_node
from app.AI.workflows.nodes.math_expert import math_expert_node
from app.AI.workflows.constants import NodeNames

@dataclass
class NodeInfo:
    """Information about a node in the workflow"""
    name: str
    description: str
    capabilities: List[str]
    example_queries: List[str]
    node_function: Callable[[ChatWorkflowState], Any]

# Node Registry containing metadata for each node
WORKER_REGISTRY: Dict[str, NodeInfo] = {
    NodeNames.MATH_EXPERT.value: NodeInfo(
        name=NodeNames.MATH_EXPERT.value,
        description="A specialized agent for solving mathematical problems and providing step-by-step explanations",
        capabilities=[
            "Solve mathematical equations and problems",
            "Provide step-by-step explanations",
            "Handle arithmetic calculations using calculator tool",
            "Break down complex problems into manageable steps"
        ],
        example_queries=[
            "What is the derivative of x^2?",
            "Solve the equation 2x + 5 = 15",
            "Calculate the area of a circle with radius 5",
            "Explain how to solve quadratic equations"
        ],
        node_function=math_expert_node
    ),
    NodeNames.MAP_SEARCHER.value: NodeInfo(
        name=NodeNames.MAP_SEARCHER.value,
        description="An agent specialized in providing map and location-based information",
        capabilities=[
            "Search for locations and places",
            "Provide weather information",
            "Get directions and routes",
            "Find nearby points of interest"
        ],
        example_queries=[
            "What's the weather in Beijing?",
            "How do I get to the nearest hospital?",
            "Find restaurants near me",
            "What's the distance between New York and Los Angeles?"
        ],
        node_function=map_searcher_node
    ),
    NodeNames.RESEARCHER.value: NodeInfo(
        name=NodeNames.RESEARCHER.value,
        description="An agent for conducting research and gathering information on various topics",
        capabilities=[
            "Search and gather information",
            "Summarize research findings",
            "Provide detailed explanations",
            "Cite sources and references"
        ],
        example_queries=[
            "What are the latest developments in AI?",
            "Research the history of the Roman Empire",
            "Find information about climate change",
            "What are the benefits of meditation?"
        ],
        node_function=researcher_node
    ),
    NodeNames.GENERAL_RESPONSE.value: NodeInfo(
        name=NodeNames.GENERAL_RESPONSE.value,
        description="A fallback agent for handling general queries when no specialized agent is suitable",
        capabilities=[
            "Handle general questions",
            "Provide conversational responses",
            "Answer non-specialized queries",
            "Maintain context in conversation"
        ],
        example_queries=[
            "How are you today?",
            "Tell me a joke",
            "What's your favorite color?",
            "Can you help me with something?"
        ],
        node_function=general_response_node
    )
}

__all__ = ["WORKER_REGISTRY", "NodeNames"]