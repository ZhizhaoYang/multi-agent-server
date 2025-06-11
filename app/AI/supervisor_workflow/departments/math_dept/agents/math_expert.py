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
_system_prompt = """
        You are a math expert. You are given a task to solve a math problem.
        You need to use the calculator tool to solve the problem.
        You need to return the result of the calculation.

        Few shot examples:
        Task: Calculate the result of the expression '2 + 3 * (4 / 2)'
        Expected Output: The result of the expression '2 + 3 * (4 / 2)' is 7

        """

_human_prompt = """
        Task Description: {description}
        Expected Output: {expected_output}
        """

prompt = ChatPromptTemplate.from_messages([
    ("system", _system_prompt),
    ("user", _human_prompt)
])



math_expert_agent = create_react_agent(
    model=llm,
    tools=[calculator],
    prompt=prompt,
)