from google import genai
from google.genai import types

# Import Client and types are not needed here, access via genai alias

client = genai.Client() # Access Client via the genai alias

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-04-17",
    contents="Explain the Occam's Razor concept and provide everyday examples of it",
    config=genai.types.GenerateContentConfig( # Access types via the genai alias
        thinking_config=genai.types.ThinkingConfig(thinking_budget=1024)
    ),
)

print(response.text)
