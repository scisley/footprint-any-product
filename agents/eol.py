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

class EOLResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the end-of-life process in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the end-of-life LCA process.")

# Load prompts from YAML
_PROMPTS_FILE = Path(__file__).parent / "prompts.yaml"
with open(_PROMPTS_FILE, 'r') as f:
    _prompts_data = yaml.safe_load(f)

eol_agent_prompt_text = _prompts_data['eol_agent_prompt']

eol_agent = create_react_agent(
    model=ChatOpenAI(model_name="gpt-4.1-2025-04-14"),
    tools=[emissions_factor_finder_tool, calculator],
    prompt=eol_agent_prompt_text,
    response_format=EOLResponse,
    name="eol_agent"
)

async def eol_phase(state: FootprintState):
    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["long_description"]}"""
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
