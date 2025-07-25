from langchain_tavily import TavilySearch
from langchain_core.tools import tool
import os

API_KEY = os.getenv("TAVILY_API_KEY")

tavily_tool = TavilySearch(
    api_key=API_KEY,
    max_results=5,
)

@tool
async def tavily_search_tool(query: str) -> str:
    """Searches the web for the given query using Tavily Search API."""
    return await tavily_tool.ainvoke({"query": query})
