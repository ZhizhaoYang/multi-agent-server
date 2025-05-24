import os
from dotenv import load_dotenv, find_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient, SSEConnection

load_dotenv(find_dotenv())

GAODE_SSE_URL = os.getenv("GAODE_SSE_URL", "")


config_gaode: SSEConnection = {
    "url": GAODE_SSE_URL,
    "transport": "sse",
    "headers": {},
    "timeout": 10,
    "sse_read_timeout": 10,
    "session_kwargs": {},
}

# Global client instance used by this module
gaode_client = MultiServerMCPClient({"gaode_map": config_gaode})
_gaode_client_is_initialized = False


async def initialize_client():
    """Initializes the global Gaode MCP client session."""
    global _gaode_client_is_initialized
    if not _gaode_client_is_initialized:
        await gaode_client.__aenter__()
        _gaode_client_is_initialized = True


async def close_client():
    """Shuts down the global Gaode MCP client session."""
    global _gaode_client_is_initialized
    if _gaode_client_is_initialized:
        await gaode_client.__aexit__(None, None, None)
        _gaode_client_is_initialized = False


async def get_gaode_tools():
    """
    Get tools from the globally managed Gaode map client.
    Ensures the client is initialized. If not, it initializes it.
    The client should be explicitly closed by calling close_client()
    at the application shutdown.
    """
    global _gaode_client_is_initialized
    if not _gaode_client_is_initialized:
        # Auto-initialize if not already initialized.
        # Consider raising an error or logging if explicit initialization is preferred.
        await initialize_client()

    return gaode_client.get_tools()
