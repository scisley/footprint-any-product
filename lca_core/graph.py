import os
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END

from lca_core.agents.state import FootprintState
from lca_core.agents.page_analysis import page_analysis_phase # Use the function from agents.page_analysis
from lca_core.agents.planner import planner_phase
from lca_core.agents.eol import eol_phase
from lca_core.agents.materials import materials_phase
from lca_core.agents.manufacturing import manufacturing_phase
from lca_core.agents.packaging import packaging_phase
from lca_core.agents.transportation import transportation_phase
from lca_core.agents.use import use_phase
from lca_core.utils.config import ConfigSchema

def setup_graph():
    """
    Initialize and configure the LangGraph workflow.
    
    This creates a directed graph of agents where each agent specializes in 
    analyzing a different phase of the product lifecycle.
    
    Returns:
        Compiled LangGraph instance ready for execution
    """
    
    # Set up LangSmith tracing if available (for monitoring and debugging)
    if os.environ.get("LANGCHAIN_API_KEY"):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = os.environ.get("LANGCHAIN_PROJECT", "footprint-any-product")
    
    # Initialize the workflow graph
    graph_builder = StateGraph(FootprintState, config_schema=ConfigSchema)
    
    # Add page analysis node
    graph_builder.add_node("page_analysis_phase", page_analysis_phase)
    graph_builder.add_edge(START, "page_analysis_phase") # Start with page analysis

    # Add planner node to the graph using the imported planner_phase
    graph_builder.add_node("planner_phase", planner_phase)
    graph_builder.add_edge("page_analysis_phase", "planner_phase") # Planner runs after page analysis
    
    # Add all agent nodes to the graph
    graph_builder.add_node("materials_phase", materials_phase)
    graph_builder.add_node("manufacturing_phase", manufacturing_phase) # Uses imported manufacturing_phase
    graph_builder.add_node("packaging_phase", packaging_phase)
    graph_builder.add_node("transportation_phase", transportation_phase)
    graph_builder.add_node("use_phase", use_phase)
    graph_builder.add_node("eol_phase", eol_phase)
    
    # Connect planner_phase to all analysis phases
    phases = ["materials_phase", "manufacturing_phase", "packaging_phase", "transportation_phase", "use_phase", "eol_phase"]
    for phase in phases:
        graph_builder.add_edge("planner_phase", phase)
    
    # Define summarizer node to calculate total footprint
    async def summarizer(state: FootprintState) -> Dict[str, Any]:
        """
        Final node that aggregates results from all lifecycle phases 
        and calculates the total carbon footprint.
        """
        # Sum up carbon values from all phases
        total_carbon = 0
        for phase in ["materials", "manufacturing", "packaging", "transportation", "use", "eol"]:
            if phase in state and "carbon" in state[phase]:
                total_carbon += state[phase]["carbon"]
                
        summary = f"Total carbon footprint: {total_carbon} kg CO2e"
        return {"messages": [{"role": "ai", "content": summary}]}
    
    # Connect all phases to the summarizer, and summarizer to end
    graph_builder.add_node("summarizer", summarizer)
    graph_builder.add_edge(phases, "summarizer")
    graph_builder.add_edge("summarizer", END)
    
    # Compile and return the workflow graph
    return graph_builder.compile()