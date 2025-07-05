import logging
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from tools.calculator.calculator import calculator_tool
from tools.emissions_factors.emissions_factors import emissions_factor_finder_tool
from tools.image_analysis.image_analysis import analyze_image_tool
from tools.research.research import research_tool
from .product_image import ProductImage
from .state import FootprintState
from api.config import MODELS, get_prompt

logger = logging.getLogger(__name__)

class EOLResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the end-of-life process in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the end-of-life LCA process.")

eol_agent_prompt_text = get_prompt('eol_agent_prompt')

async def eol_phase(state: FootprintState, config: dict):
    """
    Analyzes the end-of-life phase of the product.
    """
    model = config["configurable"].get("model", "low")
    llm = MODELS[model]

    eol_agent = create_react_agent(
        model=llm,
        tools=[emissions_factor_finder_tool, calculator_tool, analyze_image_tool, research_tool],
        prompt=eol_agent_prompt_text,
        response_format=EOLResponse,
        name="eol_agent"
    )

    image_context = ProductImage.format_images_for_prompt(state)
    
    # Construct the input string for the agent
    input = (
        f"Brand: {state['brand']}\n"
        f"Category: {state['category']}\n"
        f"Description: {state['long_description']}\n"
        f"{image_context}"
    )
    response = await eol_agent.ainvoke({
        "messages": [{"role": "user", "content": input}]
    })
    
    # Debug the response structure
    logger.info(f"EOL Agent response keys: {response.keys()}")
    if "messages" in response:
        logger.info(f"EOL Agent has {len(response['messages'])} messages")
        
    # Create the result with additional AI messages for visibility
    result = {
        "eol": {
            "carbon": response["structured_response"].carbon, 
            "summary": response["structured_response"].summary, 
            "messages": response["messages"]
        }
    }
    
    logger.info(f"EOL Result has {len(result['eol']['messages'])} messages")
    return result
