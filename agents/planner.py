import asyncio
from typing import Dict, Any
from state import FootprintState
# PageAnalyzer import is no longer needed here

async def planner_phase(state: FootprintState) -> Dict[str, Any]:
    """
    Initial node that sets up the workflow based on pre-analyzed product details.
    Receives product characteristics (brand, category, description) from the state.
    """
    await asyncio.sleep(0.2)

    # Product details are now expected to be in the state from page_analysis_phase
    brand = state.get("brand", "N/A")
    category = state.get("category", "N/A")
    description = state.get("description", "N/A")
    product_url = state.get("url", "N/A") # Use the URL from the state

    agent_messages = [
        {"role": "ai", "content": f"Planner received product for analysis: Brand='{brand}', Category='{category}', Description='{description}' from URL '{product_url}'."},
        {"role": "ai", "content": "Initializing environmental assessment workflow..."},
        {"role": "ai", "content": "Planner is preparing to delegate tasks to specialized agents."}
    ]
    
    # The planner's role is to confirm or pass through brand, category, and description,
    # and potentially make high-level decisions.
    # It also needs to return these fields so they persist in the state for other agents.
    return {
        "planner": {
            "messages": agent_messages,
            "summary": f"Planning complete for: {state['brand']} - {state['description']}. Delegating to specialized agents.",
            "carbon": None, # Planner does not calculate carbon
        },
        "brand": brand, 
        "category": category,
        "description": description,
        "url": product_url, # Pass along the URL
        "markdown": state.get("markdown"), # Pass along markdown
        "product_image_urls": state.get("product_image_urls"), # Pass along image URLs
        # Any other fields populated by page_analysis_phase that subsequent agents might need
    }
