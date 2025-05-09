from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from tools.emissions_factors import EFState, EmissionsFactor
import os

class EPAEmissionsFactor(BaseModel):
    CO2e_factor: float = Field(description="The carbon emissions factor (use -1 if no emissions factor can be found)")
    units: Literal["kgCO2/vehicle-mile", "kgCO2/short ton-mile", "kgCO2/mmBtu", "kgCO2/gallon", "kgCO2/scf", "lbCO2/MWh", "Metric Tons CO2e / Short Ton", "N/A"] = Field(description="The units associated with the carbon emissions factor (use N/A if no appropriate emissions factor can be found)")
    description: str = Field(description="Details about the emissions factor")

def epa_ef_finder(state:EFState):
    process_desc = state["process_desc"]
    phase = state["phase"]

    ef_llm = ChatOpenAI(
        model_name="gpt-4o", 
        temperature=0,
    ).with_structured_output(EPAEmissionsFactor)
    
    base_sys_prompt = """
    You are an expert at identifying the most appropriate emission factor given
    a process description and phase (e.g. manufacturing, transportation, etc).
    Here is the data you must base your answer on. If an appropriate emissions
    factor is not present in the data, return -1 for the CO2e_factor and "N/A"
    for the units."""

    # Load and append the EPA emissions data
    data_path = os.path.join(os.path.dirname(__file__), "../..", "data", "epa", "GHG-Emission-Factors-Hub.md")
    with open(data_path, 'r') as f:
        epa_data = f.read()
    
    if epa_data is None:
        raise FileNotFoundError()
    
    sys_prompt = f"{base_sys_prompt}\n\n{epa_data}"
    
    prompt = f"What is your best estimate of the carbon emissions factor for the process: {process_desc} in this phase: {phase}?"
    response:EPAEmissionsFactor = ef_llm.invoke([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": prompt}
    ])
    #print(response)

    converted = response.model_dump()
    if converted["units"] == "lbCO2/MWh":
        converted["CO2e_factor"] = converted["CO2e_factor"] * 0.453592/1000
        converted["units"] = "kgCO2/kWh"
    elif converted["units"] == "kgCO2/mmBtu":
        converted["CO2e_factor"] = converted["CO2e_factor"] * 0.003412
        converted["units"] = "kgCO2/kWh"
    elif converted["units"] == "kgCO2/short ton-mile":
        converted["CO2e_factor"] = converted["CO2e_factor"] * 1.1023
        converted["units"] = "kgCO2/tonne-mile"

    return {
        "ef_candidates": [{
            **converted,
            "citation_desc": "The 2025 annual update of the Emission Factors Hub (January 2025)",
            "citation_url": "https://www.epa.gov/climateleadership/ghg-emission-factors-hub"
        }]
    }
