"""
Footprint-Any-Product - Carbon Footprint Analysis Backend

This service provides a WebSocket API for real-time streaming of carbon footprint 
analysis for products. It uses LangGraph to coordinate multiple specialized agents
that analyze different aspects of a product's lifecycle impact.
"""

# Standard library imports
import asyncio
import json
import os
import re
from typing import Dict, Any, Union, List

# Third-party imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

# Local application imports
from state import FootprintState
from agents.planner import planner_phase
from agents.eol import eol_phase
from agents.materials import materials_phase
from agents.manufacturing import manufacturing_phase
from agents.packaging import packaging_phase
from agents.transportation import transportation_phase
from agents.use import use_phase
import utils

# Initialize environment
utils.load_environment()

# --- FastAPI App Setup ---

# Create FastAPI app
app = FastAPI(
    title="Footprint-Any-Product API",
    description="Carbon footprint analysis for any product with real-time streaming results",
    version="1.0.0"
)

# Health check endpoint
@app.get("/")
def read_root():
    """API health check endpoint."""
    return {"status": "healthy", "service": "footprint-any-product"}

# Example parametrized endpoint (for demonstration)
@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    """Example endpoint with path and query parameters."""
    return {"item_id": item_id, "q": q}

# --- LangGraph Setup ---

def setup_graph() -> Any:
    """
    Initialize and configure the LangGraph workflow.
    
    This creates a directed graph of agents where each agent specializes in 
    analyzing a different phase of the product lifecycle.
    
    Returns:
        Compiled LangGraph instance ready for execution
    """
    # Get API key from environment
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    # Configure LLM
    model = ChatOpenAI(
        model_name="gpt-4o", 
        temperature=0,
        openai_api_key=openai_api_key
    )
    
    # Set up LangSmith tracing if available (for monitoring and debugging)
    if os.environ.get("LANGCHAIN_API_KEY"):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = os.environ.get("LANGCHAIN_PROJECT", "footprint-any-product")
    
    # Initialize the workflow graph
    graph_builder = StateGraph(FootprintState)
    
    # Add planner node to the graph using the imported planner_phase
    graph_builder.add_node("planner_phase", planner_phase)
    graph_builder.add_edge(START, "planner_phase")
    
    # Add all agent nodes to the graph
    graph_builder.add_node("materials_phase", materials_phase)
    graph_builder.add_node("manufacturing_phase", manufacturing_phase) # Uses imported manufacturing_phase
    graph_builder.add_node("packaging_phase", packaging_phase)
    graph_builder.add_node("transportation_phase", transportation_phase)
    graph_builder.add_node("use_phase", use_phase)
    graph_builder.add_node("eol_phase", eol_phase)
    
    # Connect planner_phase to all analysis phases
    phases = ["materials_phase", "manufacturing_phase", "packaging_phase", "transportation_phase", "use_phase", "eol_phase"]
    for phase in phases:
        graph_builder.add_edge("planner_phase", phase)
    
    # Define summarizer node to calculate total footprint
    async def summarizer(state: FootprintState) -> Dict[str, Any]:
        """
        Final node that aggregates results from all lifecycle phases 
        and calculates the total carbon footprint.
        """
        # Sum up carbon values from all phases
        total_carbon = 0
        for phase in ["materials", "manufacturing", "packaging", "transportation", "use", "eol"]:
            if phase in state and "carbon" in state[phase]:
                total_carbon += state[phase]["carbon"]
                
        summary = f"Total carbon footprint: {total_carbon} kg CO2e"
        return {"messages": [{"role": "ai", "content": summary}]}
    
    # Connect all phases to the summarizer, and summarizer to end
    graph_builder.add_node("summarizer", summarizer)
    graph_builder.add_edge(phases, "summarizer")
    graph_builder.add_edge("summarizer", END)
    
    # Compile and return the workflow graph
    return graph_builder.compile()

# --- WebSocket Streaming Helpers ---

async def send_agent_messages(websocket: WebSocket, phase_key: str, messages: List[Dict[str, Any]]) -> None:
    """
    Extract and send meaningful agent messages to the client using standardized formats.
    
    Message format specifications:
    - Agent thinking: "Agent({agent_name}): {thought_content}"
    - Agent action: "AgentAction({agent_name}): {action_description}"
    - Agent tool use: "AgentTool({agent_name}): {tool_name}({tool_args})"
    - Agent observation: "AgentObs({agent_name}): {observation_content}"
    
    Args:
        websocket: The active WebSocket connection
        phase_key: The lifecycle phase being processed (e.g., "manufacturing")
        messages: List of message objects from the agent's output
    """
    if not messages:
        return
    
    # First send a debug message about how many messages we're processing
    message_count = len(messages)
    await websocket.send_text(f"SystemMessage: Processing {message_count} messages from {phase_key}")
    await asyncio.sleep(0.1)
    
    # Collect all message content for DEBUG
    all_content = []
    for msg in messages:
        if isinstance(msg, dict) and isinstance(msg.get("content"), str):
            all_content.append(msg.get("content", "").strip())
            
    # Print the first message to debug what's going on
    if all_content:
        first_msg = all_content[0][:100] + "..." if len(all_content[0]) > 100 else all_content[0]
        print(f"First message content sample: {first_msg}")
    
    # Track which ReAct patterns we've found to report a summary
    found_react_patterns = set()
    tool_calls_found = 0
    
    # Check for messages with "Thought:", "Action:", or "Observation:" prefixes
    for msg in messages:
        if not (isinstance(msg, dict) and isinstance(msg.get("content"), str)):
            continue
            
        content = msg.get("content", "").strip()
        role = msg.get("role", "")
        
        # For LangGraph ReAct agent messages, they use special patterns
        if "action_type" in msg or "tool_input" in msg:
            found_react_patterns.add("LangGraph")
            action_type = msg.get("action_type", "")
            tool_name = msg.get("name", "")
            tool_input = msg.get("tool_input", "")
            
            if action_type == "tool" and tool_name:
                tool_calls_found += 1
                await websocket.send_text(f"AgentTool({phase_key}): {tool_name}({json.dumps(tool_input)})")
                await asyncio.sleep(0.1)
                continue
        
        # Try to detect if this is an observation (result of a tool)
        if role == "observation" or role == "function":
            await websocket.send_text(f"AgentObs({phase_key}): {content}")
            await asyncio.sleep(0.1)
            continue
        
        # Common ReAct prefixes to look for with standard formatting
        for pattern in ["Thought:", "Action:", "Observation:"]:
            if pattern in content:
                found_react_patterns.add(pattern)
        
        # Check for Thought: pattern
        if "Thought:" in content:
            thought_pattern = r"Thought:\s*(.*?)(?=\n[A-Za-z]+:|$)"
            thought_matches = re.findall(thought_pattern, content, re.DOTALL)
            
            for thought in thought_matches:
                thought_text = thought.strip()
                if len(thought_text) > 10:
                    await websocket.send_text(f"Agent({phase_key}): {thought_text}")
                    await asyncio.sleep(0.15)
        
        # Check for Action: pattern (tool calls)
        if "Action:" in content:
            action_pattern = r"Action:\s*(.*?)(?=\n[A-Za-z]+:|$)"
            action_matches = re.findall(action_pattern, content, re.DOTALL)
            
            for action in action_matches:
                action_text = action.strip()
                
                # Look for different tool call patterns
                tool_pattern = r'([A-Za-z_]+)\s*\((?:["\'](.*?)["\']|\{(.*?)\})\)'
                tool_match = re.search(tool_pattern, action_text)
                if tool_match:
                    tool_calls_found += 1
                    tool_name = tool_match.group(1)
                    tool_args = tool_match.group(2) or tool_match.group(3) or ""
                    await websocket.send_text(f"AgentTool({phase_key}): {tool_name}(\"{tool_args}\")")
                else:
                    await websocket.send_text(f"AgentAction({phase_key}): {action_text}")
                
                await asyncio.sleep(0.15)
        
        # Check for Observation: pattern (tool results)
        if "Observation:" in content:
            obs_pattern = r"Observation:\s*(.*?)(?=\n[A-Za-z]+:|$)"
            obs_matches = re.findall(obs_pattern, content, re.DOTALL)
            
            for obs in obs_matches:
                obs_text = obs.strip()
                if len(obs_text) > 5:
                    await websocket.send_text(f"AgentObs({phase_key}): {obs_text}")
                    await asyncio.sleep(0.15)
    
    # If we didn't find ReAct patterns, look for regular agent messages
    if not found_react_patterns and tool_calls_found == 0:
        sent_count = 0
        for msg in messages:
            if not (isinstance(msg, dict) and msg.get("role") == "ai"):
                continue
                
            content = msg.get("content", "").strip()
            
            # Only send substantive content (limit to 3 messages)
            if len(content) > 15 and sent_count < 3:
                await websocket.send_text(f"Agent({phase_key}): {content}")
                await asyncio.sleep(0.2)
                sent_count += 1
    
    # Always check for special message types that might be directly from an agent
    for msg in messages:
        if isinstance(msg, dict) and isinstance(msg.get("content"), str):
            content = msg.get("content", "").strip()
            
            # For explicitly formatted agent outputs
            if content.startswith("Processing") and phase_key in content:
                await websocket.send_text(f"Agent({phase_key}): {content}")
                await asyncio.sleep(0.1)
            elif content.startswith("Evaluating") and "options" in content:
                await websocket.send_text(f"Agent({phase_key}): {content}")
                await asyncio.sleep(0.1)
            elif content.startswith("Calculated") and "carbon" in content and "impact" in content:
                await websocket.send_text(f"Agent({phase_key}): {content}")
                await asyncio.sleep(0.1)
                
    # Send status information
    if tool_calls_found > 0:
        await websocket.send_text(f"AgentStatus({phase_key}): Used {tool_calls_found} tools")
    
    # Send a summary of processing complete
    await websocket.send_text(f"SystemMessage: {phase_key} phase processing complete")

async def process_phase_update(websocket: WebSocket, phase_key: str, data: Dict[str, Any]) -> None:
    """
    Process updates for a specific lifecycle phase and send formatted updates to client.
    
    Standardized message formats:
    - "PhaseStart: {phase_key}" - Indicates the start of a new phase
    - "Agent({phase_key}): {content}" - Regular agent thoughts
    - "AgentAction({phase_key}): {action}" - Agent actions
    - "AgentTool({phase_key}): {tool_name}({args})" - Agent tool usage
    - "AgentObs({phase_key}): {observation}" - Agent observations
    - "PhaseSummary({phase_key}): {summary}" - Phase summary
    - "PhaseCarbon({phase_key}): {carbon_value}" - Phase carbon footprint value
    
    Args:
        websocket: The active WebSocket connection
        phase_key: The lifecycle phase being processed (e.g., "manufacturing")
        data: Phase data from LangGraph update
    """
    print(f"Processing {phase_key} phase")
    
    # Send phase header first (only once)
    await websocket.send_text(f"PhaseStart: {phase_key}")
    await asyncio.sleep(0.1)
    
    # Handle agent messages if available
    if "messages" in data and isinstance(data["messages"], list):
        message_count = len(data["messages"])
        if message_count > 0:
            print(f"Found {message_count} messages for {phase_key}")
            await send_agent_messages(websocket, phase_key, data["messages"])
    
    # Send the phase carbon footprint if available
    if "carbon" in data:
        await websocket.send_text(f"PhaseCarbon({phase_key}): {data['carbon']}")
        await asyncio.sleep(0.1)
    
    # Send the phase summary if available
    if "summary" in data:
        await websocket.send_text(f"PhaseSummary({phase_key}): {data['summary']}")
        await asyncio.sleep(0.1)

async def process_summarizer_update(websocket: WebSocket, data: Dict[str, Any]) -> None:
    """
    Process the final summary data and send formatted results to client.
    
    Standardized message formats:
    - "SystemMessage: {content}" - System informational messages
    - "FinalSummary: {content}" - Final analysis summary
    - "CarbonFootprint: {value}" - Specific carbon footprint value
    
    Args:
        websocket: The active WebSocket connection
        data: Summary data from LangGraph update
    """
    print("Processing final summary")
    await websocket.send_text("SystemMessage: Generating final carbon footprint summary...")
    
    # Extract summary from messages
    if "messages" in data:
        for msg in data["messages"]:
            if not (isinstance(msg, dict) and msg.get("role") == "ai"):
                continue
                
            summary_text = msg.get("content", "").strip()
            if summary_text:
                await websocket.send_text(f"FinalSummary: {summary_text}")
                
                # Attempt to extract a numeric carbon footprint if available
                carbon_match = re.search(r'(\d+\.?\d*)\s*kg\s*CO2', summary_text)
                if carbon_match:
                    carbon_value = carbon_match.group(1)
                    await websocket.send_text(f"CarbonFootprint: {carbon_value}")
                
                # Ensure it mentions carbon footprint for clarity
                if "footprint" not in summary_text.lower():
                    carbon_text = f"Total carbon footprint: {summary_text}"
                    await websocket.send_text(f"FinalSummary: {carbon_text}")
                return
    
    # Fallback if no summary found
    print("No valid summary found in messages")
    if isinstance(data, dict) and "carbon" in data:
        carbon_value = data["carbon"]
        await websocket.send_text(f"FinalSummary: Total carbon footprint: {carbon_value} kg CO2e")
        await websocket.send_text(f"CarbonFootprint: {carbon_value}")

# --- WebSocket API Endpoint ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming real-time carbon footprint analysis.
    
    This endpoint:
    1. Accepts a product URL or name from the client
    2. Runs the LangGraph workflow to analyze the product
    3. Streams real-time updates from the agent system back to the client
    
    All messages follow standardized formats:
    - "SystemMessage: {content}" - System info messages
    - "PhaseStart: {phase_key}" - Start of phase analysis
    - "Agent({phase_key}): {content}" - Agent thinking
    - "AgentAction({phase_key}): {action}" - Agent actions
    - "AgentTool({phase_key}): {tool_name}({args})" - Tool usage
    - "AgentObs({phase_key}): {observation}" - Observations
    - "PhaseSummary({phase_key}): {summary}" - Phase summary
    - "PhaseCarbon({phase_key}): {carbon_value}" - Phase carbon footprint value
    - "FinalSummary: {content}" - Final analysis summary
    - "CarbonFootprint: {value}" - Total carbon footprint value
    - "AnalysisComplete" - Analysis finished message
    - "ErrorMessage: {error}" - Error messages
    """
    await websocket.accept()
    
    # Send an immediate confirmation that the connection is established
    await websocket.send_text("SystemMessage: WebSocket connection established")
    
    try:
        # Receive the product details from the client
        data = await websocket.receive_text()
        request_data = json.loads(data)
        product_brand = request_data.get("brand", "")
        product_category = request_data.get("category", "")
        product_description = request_data.get("description", "")

        # Initial messages to client
        await websocket.send_text("SystemMessage: Starting carbon footprint analysis")
        await websocket.send_text("SystemMessage: Processing carbon footprint analysis in real-time")
        
        # Initialize and run the LangGraph workflow
        graph = setup_graph()
        config = {"configurable": {"thread_id": "websocket-session"}}
        
        # Stream the workflow execution
        stream = graph.astream(
            {
                "user_input": f"Brand: {product_brand}, Category: {product_category}, Description: {product_description}",
                "brand": product_brand,
                "category": product_category,
                "description": product_description,
                "messages": [("human", f"Analyze carbon footprint for Brand: {product_brand}, Category: {product_category}, Description: {product_description}")]
            },
            config,
            stream_mode=["updates", "values"]
        )
        
        # Process streaming results
        async for chunk in stream:
            try:
                # More detailed debugging of chunked results
                chunk_type = type(chunk).__name__
                print(f"LangGraph chunk type: {chunk_type}")
                
                # Validate chunk format and extract data
                if not (isinstance(chunk, tuple) and len(chunk) == 2):
                    print(f"WARNING: Unexpected chunk format: {type(chunk)}")
                    # Try to salvage what we can
                    if isinstance(chunk, dict):
                        print(f"Dict chunk keys: {list(chunk.keys())}")
                        event = chunk
                        mode = "values"  # Assume it's a values chunk
                    else:
                        continue
                else:
                    mode, event = chunk
                
                # Print ALL information we get from LangGraph for debugging
                print(f"LangGraph event: mode={mode}, event_type={type(event).__name__}")
                
                # Add special handling for different stream modes
                if mode == "values" and isinstance(event, dict):
                    # Values mode contains the complete state
                    print(f"Current state keys: {list(event.keys())}")
                    
                    # Check for agent outputs and node outputs
                    # Ensure "planner" is included in the list of phases to check
                    for phase_name in ["planner", "materials", "manufacturing", "packaging", "transportation", "use", "eol"]:
                        # Check for direct phase keys in the state (event is the full state in "values" mode)
                        if phase_name in event:
                            phase_key = phase_name
                            phase_data = event[phase_name] # e.g. event["planner"] or event["materials"]
                        else:
                            continue
                            
                        print(f"Found {phase_key} in state, keys: {list(phase_data.keys()) if isinstance(phase_data, dict) else 'not a dict'}")
                        
                        # For real agent results, output a detailed debug
                        if isinstance(phase_data, dict):
                                agent_debug = {
                                    "agent": phase_key,
                                    "has_messages": "messages" in phase_data and isinstance(phase_data["messages"], list),
                                    "message_count": len(phase_data.get("messages", [])) if isinstance(phase_data.get("messages"), list) else 0,
                                    "has_summary": "summary" in phase_data,
                                    "has_carbon": "carbon" in phase_data,
                                }
                                print(f"IMPORTANT - Agent data found: {agent_debug}")
                                
                                # Always send phase data if we have it in the state, even if not in updates
                                if "carbon" in phase_data:
                                    await websocket.send_text(f"AgentStatus({phase_key}): Carbon estimate: {phase_data['carbon']} kg CO2e")
                                    await websocket.send_text(f"PhaseCarbon({phase_key}): {phase_data['carbon']}")
                                
                                # Send phase header
                                await websocket.send_text(f"PhaseStart: {phase_key}")
                                await asyncio.sleep(0.1)
                                
                                # Send messages
                                if "messages" in phase_data and isinstance(phase_data["messages"], list):
                                    msg_count = len(phase_data["messages"])
                                    await websocket.send_text(f"SystemMessage: Found {msg_count} messages for {phase_key}")
                                    await send_agent_messages(websocket, phase_key, phase_data["messages"])
                                
                                # Send summary
                                if "summary" in phase_data:
                                    await websocket.send_text(f"PhaseSummary({phase_key}): {phase_data['summary']}")
                    
                # Handle updates mode as before, but with better debugging
                if mode == "updates" and isinstance(event, dict):
                    # Process each key in the update event and print it for debugging
                    print(f"Update event keys: {list(event.keys())}")
                    
                    # First, send detailed debug info about agents
                    for key, value in event.items():
                        # Debug the update structure
                        if key in ["manufacturing", "packaging", "transportation", "use", "eol"]:
                            if isinstance(value, dict):
                                agent_debug = {
                                    "agent": key,
                                    "has_messages": "messages" in value and isinstance(value["messages"], list),
                                    "message_count": len(value.get("messages", [])) if isinstance(value.get("messages"), list) else 0,
                                    "has_summary": "summary" in value,
                                    "has_carbon": "carbon" in value,
                                }
                                print(f"Agent debug: {agent_debug}")
                                
                                # Add explicit agent status message for each agent
                                # Convert key to phase name if needed (e.g., "materials_phase" -> "materials")
                                phase_key = key
                                if key.endswith("_phase"):
                                    phase_key = key.replace("_phase", "")
                                    
                                if "carbon" in value:
                                    await websocket.send_text(f"AgentStatus({phase_key}): Carbon estimate: {value['carbon']} kg CO2e")
                                    await websocket.send_text(f"PhaseCarbon({phase_key}): {value['carbon']}")
                    
                    # Now process the updates with our helpers
                    for key, value in event.items():
                        # Convert node names to phase keys if needed
                        phase_key = key
                        if key.endswith("_phase"):
                            # Convert "materials_phase" to "materials"
                            phase_key = key.replace("_phase", "")
                            print(f"Converting node name {key} to phase key {phase_key}")
                        
                        # Handle lifecycle phase updates
                        # Handle lifecycle phase updates, including "planner"
                        if phase_key in ["planner", "materials", "manufacturing", "packaging", "transportation", "use", "eol"] and isinstance(value, dict):
                            # Ensure phase_key exists in value if value is a dict of dicts (e.g. node output)
                            if phase_key in value and isinstance(value[phase_key], dict):
                                phase_data_to_process = value[phase_key]
                                messages_count = len(phase_data_to_process.get("messages", [])) if isinstance(phase_data_to_process.get("messages"), list) else 0
                                await websocket.send_text(f"SystemMessage: Processing {phase_key} phase with {messages_count} messages")
                                await process_phase_update(websocket, phase_key, phase_data_to_process)
                            # If 'value' itself is the data for the phase (e.g. for planner_phase where node output is {"planner": data, "brand":...})
                            # This case is handled if value[phase_key] is the correct data.
                            # The previous logic for react agents was value[phase_key]
                            # For planner, if key is "planner_phase", value is {"planner": data, "brand":...}, phase_key is "planner".
                            # So value[phase_key] (i.e. value["planner"]) is correct.
                        
                        # Handle final summary
                        elif key == "summarizer":
                            await process_summarizer_update(websocket, value)
                        
                        # Handle general system messages
                        elif key == "messages" and isinstance(value, list):
                            for msg in value:
                                if isinstance(msg, dict) and msg.get("role") == "ai" and msg.get("content"):
                                    await websocket.send_text(f"SystemMessage: {msg.get('content')}")
                                    await asyncio.sleep(0.1)
                
                # Small delay between updates
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing update: {str(e)}")
                await websocket.send_text(f"ErrorMessage: {str(e)}")
        
        # Send completion message
        await websocket.send_text("AnalysisComplete")
        
    except WebSocketDisconnect:
        print("WebSocket: Client disconnected")
    except asyncio.CancelledError:
        print("WebSocket: Connection cancelled")
    except ConnectionResetError:
        print("WebSocket: Connection reset")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            if websocket.client_state.CONNECTED:
                await websocket.send_text(f"ErrorMessage: {str(e)}")
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    # Use the same port as in the frontend configuration
    uvicorn.run(app, host="127.0.0.1", port=3005)
