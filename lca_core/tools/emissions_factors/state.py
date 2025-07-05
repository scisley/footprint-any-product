import operator
from typing import Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from lca_core.utils.config import get_prompt

class EmissionsFactor(BaseModel):
    """An emissions factor for a given process and phase."""
    CO2e_factor: float = Field(description="The carbon emissions factor value.")
    units: str = Field(description=get_prompt("emssions_factor_units_description"))
    description: str = Field(description="A description of the emissions factor. Don't repeat the value, describe it's details.")
    # Can result in hallucinations
    #citation_desc: str = Field(description="A description of the citation")
    #citation_url: str = Field(description="A URL for the citation", default=None)

class EFState(TypedDict):
    ef_candidates: Annotated[list[EmissionsFactor], operator.add]
    emissions_factor: EmissionsFactor
    process_desc: str
    phase: str