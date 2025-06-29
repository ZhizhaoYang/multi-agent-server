
from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv, find_dotenv
import os
from pydantic import SecretStr
from langchain_mcp_adapters.client import MultiServerMCPClient, SSEConnection
from langgraph.prebuilt import create_react_agent
from typing import Any

from app.utils.logger import logger

load_dotenv(find_dotenv())

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GAODE_SSE_URL = os.getenv("GAODE_SSE_URL", "")

config_gaode: SSEConnection = {
    "url": GAODE_SSE_URL,
    "transport": "sse",
    "headers": {},
    "timeout": 10,
    "httpx_client_factory": None,
    "sse_read_timeout": 10,
    "session_kwargs": {},
}

# Global client instance
_client = None

async def get_mcp_client():
    """
    Get MCP client instance and tools using the new langchain-mcp-adapters 0.1.0 API
    """
    global _client
    if _client is None:
        _client = MultiServerMCPClient(connections={
            "gaode": config_gaode
        })
    return _client

async def get_mcp_tools():
    """
    Get MCP tools from the client using the new API
    """
    client = await get_mcp_client()
    try:
        tools = await client.get_tools()
        return tools
    except Exception as e:
        logger.error(f"Error getting MCP tools: {e}")
        return []