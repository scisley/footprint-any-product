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

class ManufacturingResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of manufacturing in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the manufacturing LCA process.")

manufacturing_agent = create_react_agent(
    model=ChatOpenAI(model_name="gpt-4o", temperature=0),
    tools=[emissions_factor_finder_tool, calculator],
    prompt="""
    You are a manufacturing process expert. You need to estimate the carbon footprint of
    manufacturing the product. You must provide a final response in kg of CO2e.
    
    Consider all the major manufacturing processes that would be used, such as:
    - Energy used in assembly facilities
    - Process emissions (e.g., semiconductor fabrication)
    - Chemical treatments and coatings
    - Machining and forming operations
    - Quality testing and validation
    
    For each manufacturing process:
    1. Estimate the approximate energy/resource requirements
    2. Research the emissions factor for the process
    3. Calculate the carbon impact
    
    Consider both direct manufacturing emissions and emissions from the energy sources
    used in the factories where the product is made.
    
    Use your tools, but if unknown values remain, use reasonable assumptions.
    """,
    response_format=ManufacturingResponse,
    name="manufacturing_agent"
)

async def manufacturing_phase(state: FootprintState):
    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["description"]}\nWeight: {state.get("weight_kg", 0)} kg\nMaterials: {state.get("material_description", "")}"""
    response = await manufacturing_agent.ainvoke({
        "messages": [{"role": "user", "content": input}]
    })
    
    # Debug the response structure
    logger.info(f"Manufacturing Agent response keys: {response.keys()}")
    if "messages" in response:
        logger.info(f"Manufacturing Agent has {len(response['messages'])} messages")
    
    # Create the result with additional AI messages for visibility
    result = {
        "manufacturing": {
            "carbon": response["structured_response"].carbon, 
            "summary": response["structured_response"].summary, 
            "messages": response["messages"] + [
                {"role": "ai", "content": "Analyzing manufacturing processes for this product..."},
                {"role": "ai", "content": "Evaluating factory energy usage and process emissions..."},
                {"role": "ai", "content": f"Calculated total manufacturing carbon impact: {response['structured_response'].carbon} kg CO2e"}
            ]
        }
    }
    
    logger.info(f"Manufacturing Result has {len(result['manufacturing']['messages'])} messages")
    return result