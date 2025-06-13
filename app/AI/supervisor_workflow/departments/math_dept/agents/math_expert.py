from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from app.AI.core.llm import LLMFactory, LLMConfig, LLMProviders
from app.AI.supervisor_workflow.departments.math_dept.tools.calculator import calculator

llm = LLMFactory.create_llm(
    LLMConfig(
        provider=LLMProviders.DEEPSEEK.value,
        model="deepseek-chat",
        temperature=1.0,
    )
)

def create_math_expert_prompt(description: str, expected_output: str) -> str:
    """
    Create a math expert system prompt with bound variables.
    This is the core prompt creation function for math problem solving.

    Args:
        description: The task description from the user
        expected_output: The expected output format/requirements

    Returns:
        Formatted system prompt string with bound variables
    """
    return f"""You are a math expert. You are given a task to solve a math problem.
You need to use the calculator tool to solve the problem.
You need to return the result of the calculation.

Few shot examples:
Task: Calculate the result of the expression '2 + 3 * (4 / 2)'
Expected Output: The result of the expression '2 + 3 * (4 / 2)' is 7

Task Description: {description}
Expected Output: {expected_output}

Please solve this math problem step by step using the calculator tool."""

def create_math_expert_agent(description: str, expected_output: str):
    """
    Create a math expert agent with dynamically bound prompt variables.
    This avoids weird state coupling by creating the agent with variables already bound.

    Args:
        description: The task description from the user
        expected_output: The expected output format/requirements

    Returns:
        Configured create_react_agent with bound prompt
    """
    system_prompt = create_math_expert_prompt(description, expected_output)

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])

    return create_react_agent(
        model=llm,
        tools=[calculator],
        prompt=prompt_template,
    )