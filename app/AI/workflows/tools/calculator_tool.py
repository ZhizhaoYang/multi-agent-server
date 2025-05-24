from langchain_core.tools import tool
from pydantic import BaseModel, Field
import ast
import operator as op

# Supported operators
# More can be added as needed (e.g., op.pow, math functions)
_SUPPORTED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}

# Supported names (e.g., constants like pi, e, or functions like sin, cos)
# For now, empty. Could add math.pi, math.e, etc.
_SUPPORTED_NAMES = {}

def _eval_expr(node: ast.AST) -> float:
    """Safely evaluate an expression node."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        else:
            raise ValueError(f"Unsupported constant value type: {type(node.value).__name__}")
    elif isinstance(node, ast.Name):
        if node.id in _SUPPORTED_NAMES:
            return _SUPPORTED_NAMES[node.id]
        else:
            raise ValueError(f"Unsupported name: {node.id}")
    elif isinstance(node, ast.BinOp):
        left = _eval_expr(node.left)
        right = _eval_expr(node.right)
        if type(node.op) not in _SUPPORTED_OPERATORS:
            raise TypeError(f"Unsupported operator: {type(node.op).__name__}")
        return _SUPPORTED_OPERATORS[type(node.op)](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_expr(node.operand)
        if type(node.op) not in _SUPPORTED_OPERATORS:
            raise TypeError(f"Unsupported unary operator: {type(node.op).__name__}")
        return _SUPPORTED_OPERATORS[type(node.op)](operand)
    else:
        raise TypeError(f"Unsupported expression type: {type(node).__name__}")

class CalculatorInput(BaseModel):
    expression: str = Field(description="The mathematical expression to evaluate. e.g., '2 + 2 * (3-1)/2'")

@tool("calculator_tool", args_schema=CalculatorInput)
def calculator_tool(expression: str) -> str:
    """
    Evaluates a mathematical expression and returns the result.
    Supports addition (+), subtraction (-), multiplication (*), division (/), and exponentiation (** or ^).
    Handles parentheses for order of operations.
    Example: '((2 + 3) * 4) / 5 - 1'
    """
    try:
        # Parse the expression to an AST (Abstract Syntax Tree)
        # ast.parse takes the entire source code, so we need 'eval' mode for a single expression.
        node = ast.parse(expression, mode='eval').body
        result = _eval_expr(node)
        return f"The result of '{expression}' is {result}."
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError) as e:
        return f"Error evaluating expression '{expression}': {str(e)}. Please ensure the expression is valid and uses supported operations (+, -, *, /, **)."
    except Exception as e:
        return f"An unexpected error occurred while evaluating '{expression}': {str(e)}"

# Example Usage (for testing locally):
# if __name__ == '__main__':
#     print(calculator_tool.invoke({"expression": "2+2"}))
#     print(calculator_tool.invoke({"expression": "10 / (2+3)"}))
#     print(calculator_tool.invoke({"expression": "3 * (4 - 1) + 2**3"}))
#     print(calculator_tool.invoke({"expression": "-5 + 2"}))
#     print(calculator_tool.invoke({"expression": "1/0"})) # ZeroDivisionError
#     print(calculator_tool.invoke({"expression": "sqrt(4)"})) # Unsupported name
#     print(calculator_tool.invoke({"expression": "2%3"})) # Unsupported operator