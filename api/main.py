# Standard library imports
import asyncio
import json
import re # re might be needed by helpers, ensure it's here if so, or remove
from typing import Dict, Any, Union # Union might not be needed directly here

# Third-party imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Local application imports
# Adjust imports to be absolute from the project root
from state import FootprintState # For type hinting initial_graph_state
# utils module might be needed for other things, or can be removed if not.
# import utils # Environment is loaded in the root main.py

# Import graph setup and streaming helpers from .graph module
from .graph import setup_graph, process_phase_update, process_summarizer_update, send_agent_messages, page_analysis_phase


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
        
        # Extract the product URL from the request_data
        product_url = request_data.get("url")

        if not product_url:
            await websocket.send_text("ErrorMessage: Product URL was not provided by the client.")
            return

        # Initial messages to client
        await websocket.send_text(f"SystemMessage: Starting carbon footprint analysis for URL: {product_url}")
        await websocket.send_text("SystemMessage: Processing carbon footprint analysis in real-time")
        
        # Initialize and run the LangGraph workflow
        graph = setup_graph()
        config = {"configurable": {"thread_id": "websocket-session"}}
        
        # Prepare the initial state for the graph, primarily with the URL
        initial_graph_state: FootprintState = { # Type hint for clarity
            "url": product_url,
            "user_input": f"Analyze product from URL: {product_url}", # This can be used by the planner if needed
            "messages": [("human", f"Analyze carbon footprint for product at URL: {product_url}")]
            # brand, category, description will be populated by the page_analysis_phase and planner_phase
        }
        
        # Stream the workflow execution
        stream = graph.astream(
            initial_graph_state, # Pass the state with the URL
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
                    # Ensure "page_analysis", "planner" are included in the list of phases to check
                    for phase_name in ["page_analysis", "planner", "materials", "manufacturing", "packaging", "transportation", "use", "eol"]:
                        # Check for direct phase keys in the state (event is the full state in "values" mode)
                        # Note: page_analysis_phase returns its data at the top level of the state, not nested under "page_analysis"
                        # Special handling for page_analysis output which is at the top level of the state
                        if phase_name == "page_analysis":
                            # Check for direct state keys updated by page_analysis_phase
                            if "brand" in event:
                                await websocket.send_text(f"PageAnalysisBrand: {event['brand']}")
                                await asyncio.sleep(0.05)
                            if "category" in event:
                                await websocket.send_text(f"PageAnalysisCategory: {event['category']}")
                                await asyncio.sleep(0.05)
                            if "short_description" in event:
                                await websocket.send_text(f"PageAnalysisShortDescription: {event['short_description']}")
                                await asyncio.sleep(0.05)
                            if "long_description" in event:
                                await websocket.send_text(f"PageAnalysisLongDescription: {event['long_description']}")
                                await asyncio.sleep(0.05)
                            if "product_image_urls" in event and isinstance(event["product_image_urls"], list):
                                try:
                                    # Send image URLs as a JSON string
                                    await websocket.send_text(f"PageAnalysisImageUrls: {json.dumps(event['product_image_urls'])}")
                                    await asyncio.sleep(0.05)
                                except Exception as json_err:
                                    print(f"Error serializing image URLs: {json_err}")
                                    # Optionally send an error message to the client
                                    # await websocket.send_text(f"ErrorMessage: Failed to send image URLs: {json_err}")
                            continue # Move to next phase_name check

                        # Check for agent outputs and node outputs (planner, materials, etc.)
                        # Iterate through potential phase keys
                        # The loop header is already defined above, this is just the check inside the loop
                        if phase_name in event and isinstance(event[phase_name], dict): # For planner and other agents
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
                        if key in ["manufacturing", "packaging", "transportation", "use", "eol"]: # These are phase keys, not node names
                            if isinstance(value, dict): # value is the data for that phase e.g. event["manufacturing"]
                                agent_debug = {
                                    "agent": key, # This is the phase_key
                                    "has_messages": "messages" in value and isinstance(value["messages"], list),
                                    "message_count": len(value.get("messages", [])) if isinstance(value.get("messages"), list) else 0,
                                    "has_summary": "summary" in value,
                                    "has_carbon": "carbon" in value,
                                }
                                print(f"Agent debug: {agent_debug}")
                                                                    
                                if "carbon" in value:
                                    await websocket.send_text(f"AgentStatus({key}): Carbon estimate: {value['carbon']} kg CO2e")
                                    await websocket.send_text(f"PhaseCarbon({key}): {value['carbon']}")
                    
                    # Now process the updates with our helpers
                    for key, value in event.items(): # key here is the node name from the graph
                        # Convert node names to phase keys if needed
                        phase_key_for_processing = key # By default, node name is phase key
                        if key.endswith("_phase"): 
                            # Convert "materials_phase" to "materials"
                            phase_key_for_processing = key.replace("_phase", "")
                            print(f"Converting node name {key} to phase key {phase_key_for_processing}")
                        
                        # Handle lifecycle phase updates, including "planner"
                        # page_analysis_phase updates are handled differently as its output is top-level state keys
                        if key == "page_analysis_phase": # This key represents the node name
                            # The 'value' here will be the dictionary returned by page_analysis_phase
                            # e.g., {"url": ..., "brand": ..., "category": ..., "description": ..., "messages": ...}
                            if isinstance(value, dict) and "messages" in value:
                                await send_agent_messages(websocket, "page_analysis", value["messages"])
                            print(f"Update from page_analysis_phase: {list(value.keys()) if isinstance(value, dict) else 'Non-dict value'}")

                        # This handles updates from the planner and other lifecycle agents.
                        # 'value' for these nodes is typically structured like: {"planner": {"messages": ..., "summary": ...}}
                        # or {"materials": {...}} if the node name was "materials_phase" and we converted it.
                        # So, we need to access value[phase_key_for_processing] if the node output is nested.
                        # However, our agent phases (materials_phase, etc.) return a dict like {"materials": data}
                        # So, 'value' will be {"materials": data}. We need to process value[phase_key_for_processing].
                        elif phase_key_for_processing in ["planner", "materials", "manufacturing", "packaging", "transportation", "use", "eol"]:
                            # Check if the actual data for the phase is nested under the phase_key_for_processing within the 'value' dict
                            if isinstance(value, dict) and phase_key_for_processing in value and isinstance(value[phase_key_for_processing], dict):
                                phase_data_to_process = value[phase_key_for_processing]
                                messages_count = len(phase_data_to_process.get("messages", [])) if isinstance(phase_data_to_process.get("messages"), list) else 0
                                await websocket.send_text(f"SystemMessage: Processing {phase_key_for_processing} phase with {messages_count} messages")
                                await process_phase_update(websocket, phase_key_for_processing, phase_data_to_process)
                            # This case handles if the node's output (value) is *directly* the data for that phase.
                            # This shouldn't happen for our current agent structure but is a fallback.
                            elif isinstance(value, dict) and not (phase_key_for_processing in value and isinstance(value[phase_key_for_processing], dict)):
                                # This means 'value' itself is the data for the phase_key_for_processing
                                # e.g. if node "materials" returned {"carbon": ..., "summary": ...} directly
                                # This is unlikely given our agent structure `return {"materials": result}`
                                print(f"Processing direct value for {phase_key_for_processing}")
                                # await process_phase_update(websocket, phase_key_for_processing, value) # Potentially process 'value' directly
                        
                        # Handle final summary
                        elif key == "summarizer": # Node name
                            if isinstance(value, dict): # value is the output of summarizer node
                                await process_summarizer_update(websocket, value)
                        
                        # Handle general system messages (if any are directly put into state under "messages" key by a node)
                        elif key == "messages" and isinstance(value, list):
                            for msg_val in value: # Iterate through the list of messages
                                if isinstance(msg_val, tuple) and len(msg_val) == 2 and msg_val[0] == "ai" and isinstance(msg_val[1], str):
                                     await websocket.send_text(f"SystemMessage: {msg_val[1]}")
                                     await asyncio.sleep(0.1)
                                elif isinstance(msg_val, dict) and msg_val.get("role") == "ai" and msg_val.get("content"):
                                    await websocket.send_text(f"SystemMessage: {msg_val.get('content')}")
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
            # Check if websocket is still available and connected before sending
            if websocket and websocket.client_state and websocket.client_state.CONNECTED:
                await websocket.send_text(f"ErrorMessage: {str(e)}")
        except Exception as send_err:
            print(f"WebSocket error sending error message: {send_err}")
