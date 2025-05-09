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

class UseResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the use phase in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the use phase LCA process.")

# Load prompts from YAML
_PROMPTS_FILE = Path(__file__).parent / "prompts.yaml"
with open(_PROMPTS_FILE, 'r') as f:
    _prompts_data = yaml.safe_load(f)

use_agent_prompt_text = _prompts_data['use_agent_prompt']

use_agent = create_react_agent(
    model=ChatOpenAI(model_name="gpt-4.1-2025-04-14"),
    tools=[emissions_factor_finder_tool, calculator],
    prompt=use_agent_prompt_text,
    response_format=UseResponse,
    name="use_agent"
)

async def use_phase(state: FootprintState):
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
