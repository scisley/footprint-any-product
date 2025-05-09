from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from tools.emissions_factors_sources.epa_emissions_factors_hub import epa_ef_finder
from tools.emissions_factors_sources.parametric_knowledge import parametric_knowledge_ef_finder
from tools.emissions_factors_state import EFState


def source_picker(state:EFState):
    # Remove invalid candidates (those with a negative factor value)
    valid_candidates = [c for c in state["ef_candidates"] if c["CO2e_factor"] >= 0]

    # If there's only one valid candidate, just return it
    if len(valid_candidates) == 1:
        return {"emissions_factor": valid_candidates[0]}
    
    class BestIndex(BaseModel):
        best_index: int = Field(description="The index (starting at zero) of the best emission factor candidate")

    ef_picker_llm = ChatOpenAI(
        model_name="gpt-4o", 
        temperature=0,
    ).with_structured_output(BestIndex)

    sys_prompt = """
    You will be provided with 2 or more CO2 emissions factor values. Evaluate
    the sources and decide which is the best fit for the supplied process and
    analysis phase. Always prefer an emissions factor with a real citation
    over an emissions factor based on parametric knowledge.
    """
    data_prompt = f"Process: {state['process_desc']}, Phase: {state['phase']}\n\n---\n\n"
    data_prompt += "\n\n".join([f"[{i}]: {c}" for i, c in enumerate(valid_candidates)])

    response:BestIndex = ef_picker_llm.invoke([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": data_prompt}
    ])

    return {"emissions_factor": valid_candidates[response.best_index]}

builder = StateGraph(EFState)
builder.add_node(source_picker)
sources = [
    parametric_knowledge_ef_finder, 
    epa_ef_finder
]
named_sources = {f"source-{i}": source for i, source in enumerate(sources)}

# Fan out
for name, source in named_sources.items():
    builder.add_node(name, source)
    builder.add_edge(START, name)

# Fan in
builder.add_edge(named_sources.keys(), "source_picker")
builder.add_edge("source_picker", END)

ef_graph = builder.compile()

@tool
def emissions_factor_finder_tool(process_desc: str, phase: str) -> float:
    """Given a process and phase, returns the most appropriate emissions factor."""
    print(f"TOOL: Emissions Factor Finder {process_desc} {phase}")

    response = ef_graph.invoke({"process_desc": process_desc, "phase": phase})

    return response["emissions_factor"]

# Test call
#emissions_factor_finder("LCD display for a cell phone", "manufacturing")
#emissions_factor_finder("Driving a freight truck", "transportation")