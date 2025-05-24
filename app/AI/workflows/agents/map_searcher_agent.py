from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv, find_dotenv
import os
from pydantic import SecretStr
from langgraph.prebuilt import create_react_agent
from typing import Any

from app.AI.workflows.mcp.clients.gaode_map_client import get_gaode_tools, initialize_client as initialize_gaode_client

load_dotenv(find_dotenv())

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

model = ChatDeepSeek(
    model="deepseek-chat",
    api_key=SecretStr(DEEPSEEK_API_KEY) if DEEPSEEK_API_KEY else None,
)

# Global agent instance
_agent = None

async def initialize() -> None:
    """Initialize the agent if not already done. Also ensures Gaode client is initialized."""
    global _agent
    await initialize_gaode_client()

    gaode_tools = await get_gaode_tools()
    print("**** gaode_tools fetched for map_searcher_agent ****") # Clarified print message
    tools = [*gaode_tools]
    _agent = create_react_agent(model, tools=tools, prompt="You are a map searcher to help user research about the map/weather information.")

async def get_map_searcher_agent():
    """Get or create the map agent."""
    global _agent
    if _agent is None:
        await initialize()

    return _agent
