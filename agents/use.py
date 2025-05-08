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

class UseResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the use phase in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the use phase LCA process.")

system_prompt = """
You are a LCA use-phase expert. You need to estimate the carbon footprint of
the use-phase of a product. You must provide a final response in kg of
CO2e. Use your tools, but if unknown values remain, use reasonable assumptions. 
"""

use_agent = create_react_agent(
    #model=ChatOpenAI(model_name="o3"),
    model=ChatOpenAI(model_name="gpt-4o", temperature=0),
    tools=[emissions_factor_finder_tool, calculator],
    prompt=system_prompt,
    response_format=UseResponse,
    name="use_agent"
)

async def use_phase(state: FootprintState):
    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["description"]}"""
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
