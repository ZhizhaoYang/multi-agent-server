from langgraph.graph import MessagesState, END
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

class ChatState:
    query: str
    messages: MessagesState

@tool
def search_web_tool(query: str):
    return "This is a test -- search_web"


@tool
def test_tool(query: str):
    return "This is a test -- search_web"
