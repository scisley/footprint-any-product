import logging
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from tools.calculator.calculator import calculator
from tools.emissions_factors.emissions_factors import emissions_factor_finder_tool
from .state import FootprintState
from api.config import MODELS, get_prompt

logger = logging.getLogger(__name__)

class UseResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the use phase in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the use phase LCA process.")

use_agent_prompt_text = get_prompt('use_agent_prompt')

async def use_phase(state: FootprintState, config: dict):
    """
    Analyzes the use phase of the product.
    """
    model = config["configurable"].get("model", "low")
    llm = MODELS[model]

    use_agent = create_react_agent(
        model=llm,
        tools=[emissions_factor_finder_tool, calculator],
        prompt=use_agent_prompt_text,
        response_format=UseResponse,
        name="use_agent"
    )

    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["long_description"]}"""
    response = await use_agent.ainvoke({
        "messages": [{"role": "user", "content": input}]
    })
    
    # Debug the response structure
    logger.info(f"Use Phase Agent response keys: {response.keys()}")
    if "messages" in response:
        logger.info(f"Use Phase Agent has {len(response['messages'])} messages")
    
    # Create the result with additional AI messages for visibility
    result = {
        "use": {
            "carbon": response["structured_response"].carbon, 
            "summary": response["structured_response"].summary, 
            "messages": response["messages"]
        }
    }
    
    logger.info(f"Use Phase Result has {len(result['use']['messages'])} messages")
    return result
