import asyncio
import json
import re
from typing import Dict, Any, List

async def send_agent_messages(websocket: Any, phase_key: str, messages: List[Dict[str, Any]]) -> None: # Changed WebSocket type to Any for now
    """
    Extract and send meaningful agent messages to the client using standardized formats.
    
    Message format specifications:
    - Agent thinking: "Agent({agent_name}): {thought_content}"
    - Agent action: "AgentAction({agent_name}): {action_description}"
    - Agent tool use: "AgentTool({agent_name}): {tool_name}({tool_args})"
    - Agent observation: "AgentObs({agent_name}): {observation_content}"
    
    Args:
        websocket: The active WebSocket connection (type Any to avoid FastAPI dependency here)
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
    
    tool_calls_found = 0

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role")
        
        if role == "ai":
            ai_content_text = msg.get("content")
            tool_calls = msg.get("tool_calls")

            # Send AI's textual content if any (thought, reasoning)
            # Ensure content is a string before stripping
            if isinstance(ai_content_text, str) and ai_content_text.strip():
                await websocket.send_text(f"Agent({phase_key}): {ai_content_text.strip()}")
                await asyncio.sleep(0.15) # Keep sleep for readability

            # Process structured tool calls
            if isinstance(tool_calls, list):
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name")
                        tool_args = tool_call.get("args")
                        # Ensure args is a dict for json.dumps, Langchain tool_calls usually have args as dict
                        if tool_name and isinstance(tool_args, dict):
                            tool_calls_found += 1
                            # Format tool args in a more readable way
                            formatted_args = {}
                            for arg_key, arg_value in tool_args.items():
                                # Truncate long string values for readability
                                if isinstance(arg_value, str) and len(arg_value) > 100:
                                    formatted_args[arg_key] = arg_value[:97] + "..."
                                else:
                                    formatted_args[arg_key] = arg_value

                            # Add tool_id if available for tracking related tool calls
                            tool_id = tool_call.get("id", "")
                            tool_message = {
                                "name": tool_name,
                                "args": formatted_args,
                                "id": tool_id
                            }
                            await websocket.send_text(f"AgentTool({phase_key}): {json.dumps(tool_message)}")
                            await asyncio.sleep(0.1) 
        
        elif role == "tool": # This is an observation/result from a tool
            tool_content = msg.get("content")
            # Get the tool call ID if available for linking observation to tool call
            tool_call_id = msg.get("tool_call_id", "")
            tool_name = msg.get("name", "")

            # Ensure content is a string before stripping
            if isinstance(tool_content, str) and tool_content.strip():
                # Format as JSON for more structured data
                obs_data = {
                    "content": tool_content.strip(),
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_name
                }
                await websocket.send_text(f"AgentObs({phase_key}): {json.dumps(obs_data)}")
                await asyncio.sleep(0.1)
                
    # Send status information
    if tool_calls_found > 0:
        await websocket.send_text(f"AgentStatus({phase_key}): Used {tool_calls_found} tools")
    
    # Send a summary of processing complete
    await websocket.send_text(f"SystemMessage: {phase_key} phase processing complete")

async def process_phase_update(websocket: Any, phase_key: str, data: Dict[str, Any]) -> None: # Changed WebSocket type to Any
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
        websocket: The active WebSocket connection (type Any to avoid FastAPI dependency here)
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

async def process_summarizer_update(websocket: Any, data: Dict[str, Any]) -> None: # Changed WebSocket type to Any
    """
    Process the final summary data and send formatted results to client.
    
    Standardized message formats:
    - "SystemMessage: {content}" - System informational messages
    - "FinalSummary: {content}" - Final analysis summary
    - "CarbonFootprint: {value}" - Specific carbon footprint value
    
    Args:
        websocket: The active WebSocket connection (type Any to avoid FastAPI dependency here)
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
