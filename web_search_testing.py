from openai import OpenAI

client = OpenAI()

def perform_web_search(query: str) -> str:
    """
    Performs a web search using the gpt-4.1 model with the web_search_preview tool.

    Args:
        query: The search query string.

    Returns:
        The output text from the web search response.
    """
    response = client.responses.create(
        model="gpt-4.1",
        tools=[{"type": "web_search_preview"}],
        input=query
    )
    return response.output_text

# Example usage (optional, can be removed if only used by 'o3')
# if __name__ == "__main__":
#     search_query = "What is the capital of France?"
#     result = perform_web_search(search_query)
#     print(f"Search results for '{search_query}':")
#     print(result)
