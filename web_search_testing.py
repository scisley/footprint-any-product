import os
import json
from openai import OpenAI

# Ensure your OPENAI_API_KEY is set as an environment variable
# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) # Or initialize like this if needed
client = OpenAI() # Assumes OPENAI_API_KEY is in environment

def perform_web_search(query: str) -> str:
    """
    Simulates performing a web search and returns a mock result.

    Args:
        query: The search query string.

    Returns:
        A string representing the search result.
    """
    print(f"Simulating web search for query: '{query}'")
    # In a real application, this would call a web search API
    return f"Mock search result for '{query}': The current world population is approximately 8.1 billion people as of late 2024."

# Define the tool schema for the o3-2025-04-16 model
# Define the tool schema for the o3-2025-04-16 model
tools = [
    {
        "type": "function",
        "name": "perform_web_search", # Moved name here
        "description": "Performs a web search to find information online.", # Moved description here
        "parameters": { # Moved parameters here
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
        "strict": True # Moved strict here - Recommended for reliable function calls
    }
]

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a helpful assistant. You have access to a web search tool. Use the `perform_web_search` tool whenever the user asks a question that requires up-to-date information or external knowledge that you might not have, such as current statistics or recent events."},
        {"role": "user", "content": "What is the *current* population of the world? Please use your search tool to find the most recent estimate."}
    ]

    # First call to the model
    print("Calling model with initial message...")
    response = client.chat.completions.create( # Use standard chat completions
        model="o3-2025-04-16",
        messages=messages, # Use standard messages parameter
        tools=tools,
        tool_choice="auto"
    )

    # Process the response
    response_message = response.choices[0].message # Get the message object

    # Check if the model wanted to call a function
    if response_message.tool_calls: # Check for tool_calls attribute
        tool_calls = response_message.tool_calls # Get the list of tool calls

        # Assuming only one tool call for this example
        tool_call = tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        tool_call_id = tool_call.id # Get the tool call ID

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
        # Append the model's response containing the tool call
        messages.append(response_message)
        # Append the function output
        messages.append({
            "role": "tool", # Use 'tool' role
            "tool_call_id": tool_call_id, # Use the tool call ID
            "content": function_output, # Use 'content' for the output
        })

        # Second call to the model with function output
        print("\nCalling model again with function output...")
        second_response = client.chat.completions.create( # Use standard chat completions
            model="o3-2025-04-16",
            messages=messages, # Pass the updated messages list
            tools=tools, # Include tools again in case another call is needed
        )

        print("\nFinal response from model:")
        print(second_response.choices[0].message.content) # Get the final message content

    else:
        # Model did not call a function, print its direct response
        print("\nModel did not request a function call. Direct response:")
        print(response_message.content) # Get the direct message content
