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

class EOLResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the end-of-life process in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the end-of-life LCA process.")

system_prompt = """
You are a end-of-life expert. You need to estimate the carbon footprint of
the end-of-life for a product. You must provide a final response in kg of
CO2e. Use your tools, but if unknown values remain, use reasonable assumptions. 
"""

logger.info(f"Creating EOL agent with OPENAI_API_KEY: {bool(os.environ.get('OPENAI_API_KEY'))}")
# Pass the API key explicitly
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OPENAI_API_KEY not found in environment variables!")

eol_agent = create_react_agent(
    #model=ChatOpenAI(model_name="o3"),
    model=ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key=openai_api_key),
    tools=[emissions_factor_finder_tool, calculator],
    prompt=system_prompt,
    response_format=EOLResponse,
    name="eol_agent"
)

async def eol_phase(state: FootprintState):
    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["description"]}"""
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
            "messages": response["messages"] + [
                {"role": "ai", "content": "Processing end-of-life information for this product..."},
                {"role": "ai", "content": "Evaluating recycling and disposal options..."},
                {"role": "ai", "content": f"Calculated total end-of-life carbon impact: {response['structured_response'].carbon} kg CO2e"}
            ]
        }
    }
    
    logger.info(f"EOL Result has {len(result['eol']['messages'])} messages")
    return result