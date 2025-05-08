from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import os

class EmissionsFactor(BaseModel):
    """An emissions factor for a given process and phase."""
    kgCO2e: float = Field(description="The carbon emissions factor in kgCO2e.")
    units: str = Field(description="kgCO2 per what unit (e.g. per kg, per square meter, per mile, etc).")
    description: str = Field(description="A description of the emissions factor.")

# Don't initialize the LLM here - we'll initialize it when the function is called
# This prevents loading issues when the module is imported without API key set
ef_llm = None

def emissions_factor_finder(process_desc: str, phase: str) -> float:
    # Initialize the LLM when the function is called
    global ef_llm
    if ef_llm is None:
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Create the LLM with the API key
        ef_llm = ChatOpenAI(
            model_name="gpt-4o", 
            temperature=0,
            openai_api_key=api_key
        ).with_structured_output(EmissionsFactor)
    
    prompt = f"What is your best estimate of the carbon emissions factor for the process: {process_desc} in this phase: {phase}?"
    response = ef_llm.invoke([{"role": "user", "content": prompt}])
    print(response)

    return response.model_dump()

@tool
def emissions_factor_finder_tool(process_desc: str, phase: str) -> float:
    """Given a process and phase, returns the most appropriate emissions factor."""
    print(f"TOOL: Emissions Factor Finder {process_desc} {phase}")
    return emissions_factor_finder(process_desc, phase)

# Test call
#emissions_factor_finder("LCD display for a cell phone", "manufacturing")
#emissions_factor_finder("Driving a freight truck", "transportation")