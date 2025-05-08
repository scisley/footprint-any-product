import google.generativeai as genai
from google.generativeai import Client, types # Import Client and types directly

client = Client() # Use the imported Client class

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-04-17",
    contents="Explain the Occam's Razor concept and provide everyday examples of it",
    config=types.GenerateContentConfig( # Use the imported types
        thinking_config=types.ThinkingConfig(thinking_budget=1024)
    ),
)

print(response.text)
