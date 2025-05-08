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

class TransportationResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the transportation process in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the transportation LCA process.")

system_prompt = """
You are a transportation expert. You need to estimate the carbon footprint of
the transportation for a product. You must provide a final response in kg of
CO2e. Use your tools, but if unknown values remain, use reasonable assumptions. 

When using the emissions_factor_finder_tool, make sure to be specific about the
mode of transportation. For example, "road transport" is too vague, but "road
transport by truck" is better, and "Transport, freight, articulated truck |
diesel | EU average" is best.
"""

transportation_agent = create_react_agent(
    #model=ChatOpenAI(model_name="o3"),
    model=ChatOpenAI(model_name="gpt-4o", temperature=0),
    tools=[emissions_factor_finder_tool, calculator],
    prompt=system_prompt,
    response_format=TransportationResponse,
    name="transportation_agent"
)

# TODO: Update with a tool to get location information
async def transportation_phase(state: FootprintState):
    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["description"]}"""
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
