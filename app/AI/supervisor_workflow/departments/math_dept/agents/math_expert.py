from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from app.AI.core.llm import LLMFactory, LLMConfig, LLMProviders
from app.AI.supervisor_workflow.departments.math_dept.tools.calculator import calculator

llm = LLMFactory.create_llm(
    LLMConfig(
        provider=LLMProviders.OPENAI.value,
        model="gpt-4.1-nano",
        temperature=1.0,
    )
)

def create_math_expert_agent():
    """
    Create a math expert agent that outputs structured JSON responses.

    The agent responds with JSON containing both result and detailed thoughts.

    Returns:
        Configured create_react_agent with JSON output format
    """

    # System prompt for JSON structured output
    system_prompt = """You are a mathematical expert with access to a calculator tool.

Your capabilities:
- Solve complex mathematical problems step by step
- Use the calculator tool for precise calculations
- Show clear reasoning and verification of your work
- Handle algebra, arithmetic, calculus, statistics, and more

IMPORTANT: You must respond with valid JSON in this exact format:

{{
  "result": "Your final answer that directly addresses the user's question",
  "thoughts": {{
    "understanding": "Your initial understanding of what needs to be solved",
    "analysis": "Break down the key components and requirements",
    "approach": "Your strategy and methodology for solving this",
    "working": "Step-by-step calculations and work shown",
    "verification": "How you verified your solution is correct"
  }}
}}

Rules:
- Always use the calculator tool for numerical computations
- The "result" should be a clear, direct answer to the user's question
- Each thought section should be a single string (use \\n for line breaks if needed)
- Ensure valid JSON format - use proper escaping for quotes and special characters
- All thought sections are optional, but include as many as relevant

Example:
{{
  "result": "The sum of 5 + 3 is 8",
  "thoughts": {{
    "understanding": "I need to calculate the sum of two numbers: 5 and 3",
    "approach": "I will use basic addition to find the sum",
    "working": "5 + 3 = 8",
    "verification": "Confirmed: 5 + 3 = 8"
  }}
}}"""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])

    return create_react_agent(
        model=llm,
        tools=[calculator],
        prompt=prompt_template,
    )