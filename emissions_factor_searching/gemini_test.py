from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-04-17",
    contents="Explain the Occam's Razor concept and provide everyday examples of it",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=1024)
    ),
)

print(response.text)
