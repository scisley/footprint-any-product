from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tools.calculator.calculator import calculator
from tools.emissions_factors.emissions_factors import emissions_factor_finder_tool
from .state import FootprintState
import os
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class PackagingResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the packaging in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the packaging LCA process.")

# TODO: Consider updating to make it consider primary and secondary packaging.
# It's probably smart enough to know what kind of packaging the major retailers
# use :)

# Load prompts from YAML
_PROMPTS_FILE = Path(__file__).parent / "prompts.yaml"
with open(_PROMPTS_FILE, 'r') as f:
    _prompts_data = yaml.safe_load(f)

packaging_agent_prompt_text = _prompts_data['packaging_agent_prompt']

packaging_agent = create_react_agent(
    model=ChatOpenAI(model_name="gpt-4.1-2025-04-14"),
    tools=[emissions_factor_finder_tool, calculator],
    prompt=packaging_agent_prompt_text,
    response_format=PackagingResponse,
    name="packaging_agent"
)

async def packaging_phase(state: FootprintState):
    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["long_description"]}"""
    response = await packaging_agent.ainvoke({
        "messages": [{"role": "user", "content": input}]
    })
    
    # Debug the response structure
    logger.info(f"Packaging Agent response keys: {response.keys()}")
    if "messages" in response:
        logger.info(f"Packaging Agent has {len(response['messages'])} messages")
    
    # Create the result with additional AI messages for visibility
    result = {
        "packaging": {
            "carbon": response["structured_response"].carbon, 
            "summary": response["structured_response"].summary, 
            "messages": response["messages"]
        }
    }
    
    logger.info(f"Packaging Result has {len(result['packaging']['messages'])} messages")
    return result

#packaging_phase({"brand": "Apple", "category": "cellphone", "description": "An iPhone 15"})
