import os # Import the os module
import google as genai
from google.genai import types # Keep the import for types as it seems necessary

# Import Client is not needed here, access via genai alias

# Initialize the client with the API key from environment variables
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY")) # Access Client via the genai alias

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-04-17",
    contents="Explain the Occam's Razor concept and provide everyday examples of it",
    config=genai.types.GenerateContentConfig( # Access types via the genai alias
        thinking_config=genai.types.ThinkingConfig(thinking_budget=1024)
    ),
)

print(response.text)
