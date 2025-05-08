import asyncio
from typing import Dict, Any
from state import FootprintState

async def planner_phase(state: FootprintState) -> Dict[str, Any]:
    """
    Initial node that analyzes the product details and sets up the workflow.
    Takes the user input and determines product characteristics.
    """
    # Small delay to help with streaming
    await asyncio.sleep(0.2)

    # Use the brand, category, description from the state
    brand = state.get("brand", "Unknown Brand")
    category = state.get("category", "Unknown Category")
    description = state.get("description", "No description provided")
    
    # Initial agent messages showing reasoning, incorporating the dynamic product details
    agent_messages = [
        {"role": "ai", "content": f"Received product for analysis: Brand='{brand}', Category='{category}', Description='{description}'."},
        {"role": "ai", "content": "Initializing environmental assessment workflow..."},
        {"role": "ai", "content": "Planner is preparing to delegate tasks to specialized agents."}
    ]
    
    # The planner's role is now primarily to kick off the process and provide initial messages.
    # It confirms or passes through brand, category, and description.
    return {
        "planner": {
            "messages": agent_messages,
            "summary": f"Planning complete for: {brand} - {description}. Delegating to specialized agents.",
            "carbon": None, # Planner does not calculate carbon
        },
        "brand": brand, 
        "category": category,
        "description": description,
    }
