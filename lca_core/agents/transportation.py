from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from lca_core.tools.calculator.calculator import calculator_tool
from lca_core.tools.emissions_factors.emissions_factors import emissions_factor_finder_tool
from lca_core.tools.image_analysis.image_analysis import analyze_image_tool
from lca_core.tools.research.research import research_tool
from lca_core.tools.transportation.transportation import transportation_tool
from .product_image import ProductImage
from .state import FootprintState
import logging
from lca_core.utils.config import MODELS, get_prompt

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
        tools=[emissions_factor_finder_tool, calculator_tool, analyze_image_tool, research_tool, transportation_tool],
        prompt=transportation_agent_prompt_text,
        response_format=TransportationResponse,
        name="transportation_agent"
    )

    image_context = ProductImage.format_images_for_prompt(state)
    
    # Construct the input string for the agent
    input = (
        f"Brand: {state['brand']}\n"
        f"Category: {state['category']}\n"
        f"Description: {state['long_description']}\n"
        f"{image_context}"
    )
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
