from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

class EmissionsFactor(BaseModel):
    """An emissions factor for a given process and phase."""
    kgCO2e: float = Field(description="The carbon emissions factor in kgCO2e.")
    units: str = Field(description="kgCO2 per what unit (e.g. per kg, per square meter, per mile, etc).")
    description: str = Field(description="A description of the emissions factor.")
    
ef_llm = ChatOpenAI(model_name="gpt-4o", temperature=0).with_structured_output(EmissionsFactor)

def emissions_factor_finder(process_desc: str, phase: str) -> float:
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