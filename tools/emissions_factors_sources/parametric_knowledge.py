from tools.emissions_factors import EFState, EmissionsFactor
from langchain_openai import ChatOpenAI

def parametric_knowledge_ef_finder(state: EFState):
    process_desc = state["process_desc"]
    phase = state["phase"]

    ef_llm = ChatOpenAI(
        model_name="gpt-4o", 
        temperature=0,
    ).with_structured_output(EmissionsFactor)
    
    prompt = f"What is your best estimate of the carbon emissions factor for the process: {process_desc} in this phase: {phase}?"
    response = ef_llm.invoke([{"role": "user", "content": prompt}])

    return {
        "ef_candidates": [{
            **response.model_dump(),
            "citation_desc": "parametric knowledge",
            "citation_url": "N/A"
        }]
    }
