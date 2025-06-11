from langgraph.prebuilt import create_react_agent

from app.AI.supervisor_workflow.departments.web_dept.tools.tavily_search import tavily_search_tool
from app.AI.core.llm import LLMFactory, LLMConfig, LLMProviders

llm = LLMFactory.create_llm(
    LLMConfig(
        provider=LLMProviders.DEEPSEEK.value,
        model="deepseek-chat",
        temperature=1.0,
    )
)

web_search_prompt = """Please perform a web search to address the following task.

Task Description:
{description}

Explanation of the expected output:
{expected_output}

Provide a comprehensive answer based on your search results.
"""

web_searcher_agent = create_react_agent(
    llm, tools=[tavily_search_tool], prompt=web_search_prompt,
)
