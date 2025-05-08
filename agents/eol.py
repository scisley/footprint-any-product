from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tools.calculator import calculator
from tools.emissions_factors import emissions_factor_finder_tool
from state import FootprintState

class EOLResponse(BaseModel):
    carbon: float = Field(description="The carbon footprint of the end-of-life process in kg of CO2e.")
    summary: str = Field(description="A 2 sentence summary of the end-of-life LCA process.")

system_prompt = """
You are a end-of-life expert. You need to estimate the carbon footprint of
the end-of-life for a product. You must provide a final response in kg of
CO2e. Use your tools, but if unknown values remain, use reasonable assumptions. 
"""

eol_agent = create_react_agent(
    #model=ChatOpenAI(model_name="o3"),
    model=ChatOpenAI(model_name="gpt-4o", temperature=0),
    tools=[emissions_factor_finder_tool, calculator],
    prompt=system_prompt,
    response_format=EOLResponse,
    name="eol_agent"
)

def eol_phase(state: FootprintState):
    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["description"]}"""
    response = eol_agent.invoke({
        "messages": [{"role": "user", "content": input}]
    })
    return {
        "eol": {
            "carbon": response["structured_response"].carbon, 
            "summary": response["structured_response"].summary, 
            "messages": response["messages"]
        }
    }