from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from lca_core.tools.emissions_factors.state import EFState
from pathlib import Path
from lca_core.utils.config import get_prompt
from lca_core.utils import Q_

class EPAEmissionsFactor(BaseModel):
    CO2e_factor: float = Field(description="The carbon emissions factor (use -1 if no emissions factor can be found)")
    units: Literal["kgCO2/vehicle_mile", "kgCO2/(short_ton*mile)", "kgCO2/mmBtu", "kgCO2/gallon", "kgCO2/scf", "lbCO2/MWh", "tCO2e / short_ton", "kgCO2 / passenger_mile", "N/A"] = Field(description=get_prompt("emssions_factor_units_description"))
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
    data_path = Path(__file__).parent / "GHG-Emission-Factors-Hub.md"
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

    # Convert units to standardized form (e.g kgCO2/kWh)
    units = response.units
    CO2e_factor = response.CO2e_factor
    if units == "lbCO2/MWh":
        CO2e_factor = Q_(CO2e_factor, units).to("kgCO2/kWh").magnitude
        units = "kgCO2/kWh"
    elif units == "kgCO2/mmBtu":
        CO2e_factor = Q_(CO2e_factor, units).to("kgCO2/kWh").magnitude
        units = "kgCO2/kWh"
    elif units == "kgCO2/(short_ton*mile)":
        CO2e_factor = Q_(CO2e_factor, units).to("kgCO2/(tonne*km)").magnitude
        units = "kgCO2/(tonne*km)"

    return {
        "ef_candidates": [{
            "CO2e_factor": CO2e_factor,
            "units": units,
            "description": response.description,
            "citation_desc": "The 2025 annual update of the Emission Factors Hub (January 2025)",
            "citation_url": "https://www.epa.gov/climateleadership/ghg-emission-factors-hub"
        }]
    }
