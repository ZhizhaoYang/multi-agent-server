"""A calculator tool that can be used by an agent to evaluate mathematical expressions."""
from typing import Annotated
import numexpr

from langchain_core.tools import tool

@tool
def calculator(
    expression: Annotated[str, "A mathematical expression to evaluate. For example, '2 + 3 * (4 / 2)'."]
) -> Annotated[str, "The result of the mathematical evaluation."]:
    """
    A calculator that can evaluate mathematical expressions.
    Handles basic arithmetic operations (+, -, *, /), exponentiation (**), and parentheses.
    For example, '2 + 3 * (4 / 2)' = 7
    """
    try:
        # Using numexpr for safe evaluation of numerical expressions.
        # .item() is used to convert the numpy type to a standard Python type.
        result = numexpr.evaluate(expression).item()
        return f"The result of the expression '{expression}' is {result}."
    except KeyError as e:
        return f"Failed to evaluate the expression '{expression}'. An unknown variable or function was used: {e}"
    except Exception as e:
        return f"Failed to evaluate the expression '{expression}'. Error: {e}"
