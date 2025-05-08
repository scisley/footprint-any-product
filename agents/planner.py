import asyncio
from typing import Dict, Any
from state import FootprintState
from page_analyzer import PageAnalyzer

async def planner_phase(state: FootprintState) -> Dict[str, Any]:
    """
    Initial node that analyzes the product details and sets up the workflow.
    Takes the user input and determines product characteristics.
    """
    # Small delay to help with streaming
    await asyncio.sleep(0.2)

    page = PageAnalyzer(state["url"])
    state["url"] = page.url # trimmed url
    state["markdown"] = page.markdown
    state["product_image_urls"] = list(page.images.keys())

    state['brand'] = page.query_markdown("What is the brand of the product in the markdown below? Return only the simple brand name, not a description of the product.")
    state['category'] = page.query_markdown("What is the category of the product in the markdown below, in very simple terms, that don't include the brand or very descriptive details? For example, a bike, t-shirt, office chair, or notebook, rather than something more specific like a blue notebook or an ergonomic office chair.")
    state['description'] = page.query_markdown("What is a very brief description of the product in the markdown below? Return a single sentence, no more than 20 words.")
    
    # Initial agent messages showing reasoning, incorporating the dynamic product details
    agent_messages = [
        {"role": "ai", "content": f"Received product for analysis: Brand='{state.get('brand', 'N/A')}', Category='{state.get('category', 'N/A')}', Description='{state.get('description', 'N/A')}'."},
        {"role": "ai", "content": "Initializing environmental assessment workflow..."},
        {"role": "ai", "content": "Planner is preparing to delegate tasks to specialized agents."}
    ]
    
    # The planner's role is now primarily to kick off the process and provide initial messages.
    # It confirms or passes through brand, category, and description.
    return {
        "planner": {
            "messages": agent_messages,
            "summary": f"Planning complete for: {state.get('brand', 'N/A')} - {state.get('description', 'N/A')}. Delegating to specialized agents.",
            "carbon": None, # Planner does not calculate carbon
        },
        "brand": state.get("brand", "Unknown Brand"), 
        "category": state.get("category", "Unknown Category"),
        "description": state.get("description", "No description provided"),
    }
