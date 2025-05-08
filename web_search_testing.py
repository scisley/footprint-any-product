import os
import json
from openai import OpenAI

# Ensure your OPENAI_API_KEY is set as an environment variable
# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) # Or initialize like this if needed
client = OpenAI() # Assumes OPENAI_API_KEY is in environment

def perform_web_search(query: str) -> str:
    """
    Performs a web search using the gpt-4.1 model with the web_search_preview tool.

    Args:
        query: The search query string.

    Returns:
        The output text from the web search response.
    """
    # Note: This function directly uses the web_search_preview tool with gpt-4.1
    # It is called by the main logic when the o3-2025-04-16 model requests it.
    response = client.responses.create(
        model="gpt-4.1", # Use the model that has the web_search_preview tool
        tools=[{"type": "web_search_preview"}],
        input=query
    )
    return response.output_text

# Define the tool schema for the o3-2025-04-16 model
tools = [
    {
        "type": "function",
        "function": {
            "name": "perform_web_search",
            "description": "Performs a web search to find information online.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            },
            "strict": True # Recommended for reliable function calls
        }
    }
]

if __name__ == "__main__":
    messages = [{"role": "user", "content": "What is the current population of the world?"}]

    # First call to the model
    print("Calling model with initial message...")
    response = client.responses.create(
        model="o3-2025-04-16", # Use the model that will decide to call the function
        input=messages,
        tools=tools,
        tool_choice="auto" # Allow the model to decide whether to call the tool
    )

    # Process the response
    response_message = response.output

    # Check if the model wanted to call a function
    if response_message and isinstance(response_message, list) and response_message[0].type == "function_call":
        tool_call = response_message[0]
        function_name = tool_call.name
        function_args = json.loads(tool_call.arguments)

        print(f"Model requested to call function: {function_name} with args: {function_args}")

        # Execute the function
        if function_name == "perform_web_search":
            try:
                function_output = perform_web_search(query=function_args.get("query"))
                print("Function executed successfully.")
                print("Function output:", function_output[:200] + "..." if len(function_output) > 200 else function_output) # Print snippet
            except Exception as e:
                function_output = f"Error executing function: {e}"
                print("Function execution failed:", e)
        else:
            function_output = f"Unknown function requested: {function_name}"
            print(function_output)

        # Append the function call and function output to messages
        messages.append(tool_call)
        messages.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": function_output,
        })

        # Second call to the model with function output
        print("\nCalling model again with function output...")
        second_response = client.responses.create(
            model="o3-2025-04-16",
            input=messages,
            tools=tools, # Include tools again in case another call is needed
        )

        print("\nFinal response from model:")
        print(second_response.output_text)

    else:
        # Model did not call a function, print its direct response
        print("\nModel did not request a function call. Direct response:")
        print(response.output_text)
