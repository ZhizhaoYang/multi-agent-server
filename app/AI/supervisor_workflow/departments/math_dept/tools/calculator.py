"""A calculator tool that can be used by an agent to evaluate mathematical expressions."""
from typing import Annotated
from simpleeval import simple_eval
from app.utils.logger import logger
from langchain_core.tools import tool

@tool
def calculator(
    expression: Annotated[str, "A mathematical expression to evaluate. For example, '2 + 3 * (4 / 2)'."]
) -> Annotated[str, "The result of the mathematical evaluation."]:
    """
    A calculator that can evaluate mathematical expressions.
    Handles basic arithmetic operations (+, -, *, /), exponentiation (**), and parentheses.
    For example, '2 + 3 * (4 / 2)' = 8.0
    """
    logger.info(f"-- calculator -- evaluating: {expression}")
    try:
        # Using simpleeval for safe evaluation of numerical expressions
        result = simple_eval(expression)
        logger.info(f"The result of the expression '{expression}' is {result}.")
        return f"The result of the expression '{expression}' is {result}."
    except Exception as e:
        error_msg = f"Failed to evaluate the expression '{expression}'. Error: {e}"
        logger.error(error_msg)
        return error_msg
