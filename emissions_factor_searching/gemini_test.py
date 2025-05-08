import google.generativeai as genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-04-17",
    contents="Explain the Occam's Razor concept and provide everyday examples of it",
    config=genai.types.GenerateContentConfig(
        thinking_config=genai.types.ThinkingConfig(thinking_budget=1024)
    ),
)

print(response.text)
