from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tools.calculator import calculator
from tools.emissions_factors import emissions_factor_finder_tool
from .state import FootprintState
import os
import logging
import yaml
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaterialsResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the materials in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the materials LCA process.")

# Load prompts from YAML
_PROMPTS_FILE = Path(__file__).parent / "prompts.yaml"
with open(_PROMPTS_FILE, 'r') as f:
    _prompts_data = yaml.safe_load(f)

materials_agent_prompt_text = _prompts_data['materials_agent_prompt']

materials_agent = create_react_agent(
    model=ChatOpenAI(model_name="gpt-4.1", temperature=0),
    tools=[emissions_factor_finder_tool, calculator],
    prompt=materials_agent_prompt_text,
    response_format=MaterialsResponse,
    name="materials_agent"
)

async def materials_phase(state: FootprintState):
    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["long_description"]}"""
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
