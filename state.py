from typing import Annotated, TypedDict
from langgraph.graph import START, END
from langgraph.graph.message import add_messages
from pydantic import Field

class PhaseData(TypedDict):
    messages: list
    summary: str
    carbon: float

# Define the state that will be shared between agents
class FootprintState(TypedDict):
    messages: Annotated[list, add_messages]
    user_input: str = Field(default="")
    url: str
    brand: str
    category: str
    short_description: str
    long_description: str
    material_description: str # A natural language description of the materials in the product
    product_image_urls: list[str]
    weight_kg: float
    planner: PhaseData
    materials: PhaseData
    manufacturing: PhaseData
    packaging: PhaseData
    transportation: PhaseData
    use: PhaseData
    eol: PhaseData
