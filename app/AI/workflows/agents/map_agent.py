from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv, find_dotenv
import os
from pydantic import SecretStr
from langchain_mcp_adapters.client import MultiServerMCPClient, SSEConnection
from langgraph.prebuilt import create_react_agent
from typing import Any

load_dotenv(find_dotenv())

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GAODE_SSE_URL = os.getenv("GAODE_SSE_URL", "")

model = ChatDeepSeek(
    model="deepseek-chat",
    api_key=SecretStr(DEEPSEEK_API_KEY) if DEEPSEEK_API_KEY else None,
)

config_gaode: SSEConnection = {
    "url": GAODE_SSE_URL,
    "transport": "sse",
    "headers": {},
    "timeout": 10,
    "sse_read_timeout": 10,
    "session_kwargs": {},
}

# Global client and agent instances
_client = None
_agent = None

async def initialize() -> None:
    """Initialize the client and agent if not already done."""
    global _client, _agent
    if _client is None:
        _client = MultiServerMCPClient({"gaode_map": config_gaode})
        await _client.__aenter__()
        _agent = create_react_agent(model, _client.get_tools(), prompt="You are a map searcher to help user research about the map/weather information.")

async def get_map_agent() -> Any:
    """Get or create the map agent."""
    global _agent
    if _agent is None:
        await initialize()
    return _agent  # This will always be non-None after initialize()

# Don't create the agent here - it will be initialized on first use
