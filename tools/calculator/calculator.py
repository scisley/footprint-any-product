import numexpr
import math
from langchain_core.tools import tool

# See https://python.langchain.com/api_reference/langchain/chains/langchain.chains.llm_math.base.LLMMathChain.html
@tool
def calculator(expression: str) -> str:
    """Calculate expression using Python's numexpr library.

    Expression should be a single line mathematical expression
    that solves the problem.

    Examples:
        "37593 * 67" for "37593 times 67"
        "37593**(1/5)" for "37593^(1/5)"
        "pi * 2**2" for "pi times 2 squared"
        "e**(2*pi)" for "e to the power of 2 pi"
    """
    local_dict = {"pi": math.pi, "e": math.e}
    return str(
        numexpr.evaluate(
            expression.strip(),
            global_dict={},  # restrict access to globals
            local_dict=local_dict,  # add common mathematical functions
        )
    )