import os
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

# Import Client and types are not needed here, access via genai alias

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY")) # Access Client via the genai alias
model_id = "gemini-2.5-flash-preview-04-17"

google_search_tool = Tool(
    google_search = GoogleSearch()
)

response = client.models.generate_content(
    model=model_id,
    contents="""
Outline a comprehensive Life Cycle Assessment (LCA) for an iPhone 15 Pro 256GB.

Your response should cover the typical "cradle-to-grave" stages of the product's life cycle. For each stage, describe:

1.  **Key Activities:** What happens during this stage?
2.  **Major Inputs:** What resources (materials, energy, water) are typically consumed?
3.  **Major Outputs:** What emissions (to air, water, soil), waste, or byproducts are typically generated?
4.  **Potential Environmental Impacts:** Discuss the common environmental consequences associated with this stage (e.g., greenhouse gas emissions, water pollution, resource depletion, waste generation, toxicity).

Structure your response clearly, listing each stage as a distinct section.

**LCA Stages to Cover:**

*   **Raw Material Extraction:** (e.g., mining, drilling, harvesting)
*   **Material Processing:** (e.g., refining, manufacturing raw materials)
*   **Manufacturing:** (e.g., producing the final product)
*   **Transportation/Distribution:** (Moving materials and finished products)
*   **Use Phase:** (How the product is used by the consumer)
*   **End-of-Life:** (Disposal, recycling, composting, etc.)

Based on this outline, provide:

*   A brief summary of the key lifecycle stages and their primary environmental contributions.
*   A single, estimated overall emissions factor for the entire product lifecycle (cradle-to-grave) in kg CO2e per [unit of product, e.g., 'bottle']. Base this estimate on your training data and typical LCA methodologies. State clearly that this is a generalized estimate and real-world values vary significantly based on specific data, location, and processes.    
""",
    config=GenerateContentConfig(
        tools=[google_search_tool],
        response_modalities=["TEXT"],
    )
)

for each in response.candidates[0].content.parts:
    print(each.text)
# Example response:
# The next total solar eclipse visible in the contiguous United States will be on ...