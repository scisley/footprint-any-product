from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tools.calculator import calculator
from tools.emissions_factors import emissions_factor_finder_tool
from state import FootprintState

class PackagingResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the packaging in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the packaging LCA process.")

# TODO: Consider updating to make it consider primary and secondary packaging.
# It's probably smart enough to know what kind of packaging the major retailers
# use :)
packaging_agent = create_react_agent(
    #model=ChatOpenAI(model_name="o3"),
    model=ChatOpenAI(model_name="gpt-4o", temperature=0),
    tools=[emissions_factor_finder_tool, calculator],
    prompt="""
    You are a packaging expert. You need to estimate the carbon footprint of the
    packaging for the product. You must provide a final response in kg of CO2e.
    Use your tools, but if unknown values remain, use reasonable assumptions.
    """,
    response_format=PackagingResponse,
    name="packaging_agent"
)

def packaging_phase(state: FootprintState):
    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["description"]}"""
    response = packaging_agent.invoke({
        "messages": [{"role": "user", "content": input}]
    })
    return {
        "packaging": {
            "carbon": response["structured_response"].carbon, 
            "summary": response["structured_response"].summary, 
            "messages": response["messages"]
        }
    }

#packaging_phase({"brand": "Apple", "category": "cellphone", "description": "An iPhone 15"})