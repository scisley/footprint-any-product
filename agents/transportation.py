from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from tools.calculator.calculator import calculator
from tools.emissions_factors.emissions_factors import emissions_factor_finder_tool
from .state import FootprintState
import logging
from api.config import MODELS, get_prompt

logger = logging.getLogger(__name__)

class TransportationResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the transportation process in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the transportation LCA process.")

transportation_agent_prompt_text = get_prompt('transportation_agent_prompt')

async def transportation_phase(state: FootprintState, config: dict):
    """
    Analyzes the transportation phase of the product.
    """
    model = config["configurable"].get("model", "low")
    llm = MODELS[model]

    transportation_agent = create_react_agent(
        model=llm,
        tools=[emissions_factor_finder_tool, calculator],
        prompt=transportation_agent_prompt_text,
        response_format=TransportationResponse,
        name="transportation_agent"
    )

    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["long_description"]}"""
    response = await transportation_agent.ainvoke({
        "messages": [{"role": "user", "content": input}]
    })
    
    # Debug the response structure
    logger.info(f"Transportation Agent response keys: {response.keys()}")
    if "messages" in response:
        logger.info(f"Transportation Agent has {len(response['messages'])} messages")
    
    # Create the result with additional AI messages for visibility
    result = {
        "transportation": {
            "carbon": response["structured_response"].carbon, 
            "summary": response["structured_response"].summary, 
            "messages": response["messages"]
        }
    }
    
    logger.info(f"Transportation Result has {len(result['transportation']['messages'])} messages")
    return result

#transportation_phase({"brand": "Apple", "category": "cellphone", "description": "An iPhone 15"})
