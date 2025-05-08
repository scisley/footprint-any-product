from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tools.calculator import calculator
from tools.emissions_factors import emissions_factor_finder_tool
from state import FootprintState
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaterialsResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the materials in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the materials LCA process.")

materials_agent = create_react_agent(
    model=ChatOpenAI(model_name="gpt-4o", temperature=0),
    tools=[emissions_factor_finder_tool, calculator],
    prompt="""
    You are a materials science expert. You need to estimate the carbon footprint of the
    raw materials used in the product. You must provide a final response in kg of CO2e.
    
    Consider all the major materials that would be used in the product, such as:
    - Metals (aluminum, steel, copper, etc.)
    - Plastics and polymers
    - Glass
    - Ceramics
    - Rare earth elements
    - Textiles and fabrics
    - Wood, paper, and natural materials
    
    For each material:
    1. Estimate the approximate weight
    2. Research the emissions factor for extracting/producing the material
    3. Calculate the carbon impact
    
    Use your tools, but if unknown values remain, use reasonable assumptions.
    """,
    response_format=MaterialsResponse,
    name="materials_agent"
)

async def materials_phase(state: FootprintState):
    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["description"]}"""
    response = await materials_agent.ainvoke({
        "messages": [{"role": "user", "content": input}]
    })
    
    # Debug the response structure
    logger.info(f"Materials Agent response keys: {response.keys()}")
    if "messages" in response:
        logger.info(f"Materials Agent has {len(response['messages'])} messages")
    
    # Create the result with additional AI messages for visibility
    result = {
        "materials": {
            "carbon": response["structured_response"].carbon, 
            "summary": response["structured_response"].summary, 
            "messages": response["messages"]
        }
    }
    
    logger.info(f"Materials Result has {len(result['materials']['messages'])} messages")
    return result
