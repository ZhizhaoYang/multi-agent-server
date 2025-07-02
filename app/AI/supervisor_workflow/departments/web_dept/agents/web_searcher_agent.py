from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from app.AI.supervisor_workflow.departments.web_dept.tools.tavily_search import tavily_search_tool
from app.AI.core.llm import LLMFactory, LLMConfig, LLMProviders

llm = LLMFactory.create_llm(
    LLMConfig(
        provider=LLMProviders.OPENAI.value,
        model="gpt-4.1",
        temperature=1.0,
    )
)


def create_web_search_prompt(description: str, expected_output: str) -> str:
    """
    Create a web search system prompt with bound variables.
    This is the core prompt creation function - the placeholder for binding prompt content.

    Args:
        description: The task description from the user
        expected_output: The expected output format/requirements

    Returns:
        Formatted system prompt string with bound variables
    """
    return f"""You are a helpful web research assistant. Use the available search tools to find accurate and up-to-date information.

Please perform a web search to address the following task.

User's instructions:
{description}

Explanation of the expected output:
{expected_output}

Use your search tools to find relevant information and provide a comprehensive answer based on your search results."""


def create_web_searcher_agent(description: str, expected_output: str):
    """
    Create a web searcher agent with dynamically bound prompt variables.
    This avoids weird state coupling by creating the agent with variables already bound.

    Args:
        description: The task description from the user
        expected_output: The expected output format/requirements

    Returns:
        Configured create_react_agent with bound prompt
    """
    system_prompt = create_web_search_prompt(description, expected_output)

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])

    return create_react_agent(
        model=llm,
        tools=[tavily_search_tool],
        prompt=prompt_template,
    )
