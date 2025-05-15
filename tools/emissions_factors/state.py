import operator
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field

class EmissionsFactor(BaseModel):
    """An emissions factor for a given process and phase."""
    CO2e_factor: float = Field(description="The carbon emissions factor value.")
    units: str = Field(description="The carbon emissions factor units (e.g. kgCO2e/kg, kgCO2/square meter, kgCO2e/per mile, etc).")
    description: str = Field(description="A description of the emissions factor. Don't repeat the value, describe it's details.")
    # Can result in hallucinations
    #citation_desc: str = Field(description="A description of the citation")
    #citation_url: str = Field(description="A URL for the citation", default=None)

class EFState(TypedDict):
    ef_candidates: Annotated[list[EmissionsFactor], operator.add]
    emissions_factor: EmissionsFactor
    process_desc: str
    phase: str