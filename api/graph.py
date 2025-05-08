# Standard library imports
import asyncio
import json
import os
import re
from typing import Dict, Any, Union, List

# Third-party imports
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

# Local application imports (absolute imports from project root)
from state import FootprintState
from agents.page_analysis import page_analysis_phase # Use the function from agents.page_analysis
from agents.planner import planner_phase
from agents.eol import eol_phase
from agents.materials import materials_phase
from agents.manufacturing import manufacturing_phase
from agents.packaging import packaging_phase
from agents.transportation import transportation_phase
from agents.use import use_phase
# Note: utils is not directly used in this file after refactor,
# but load_environment is called in the root main.py

# --- LangGraph Setup ---
# The page_analysis_phase is now imported directly from agents.page_analysis
# and will be used in graph_builder.add_node("page_analysis_phase", page_analysis_phase)

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
    
    # Add page analysis node
    graph_builder.add_node("page_analysis_phase", page_analysis_phase)
    graph_builder.add_edge(START, "page_analysis_phase") # Start with page analysis

    # Add planner node to the graph using the imported planner_phase
    graph_builder.add_node("planner_phase", planner_phase)
    graph_builder.add_edge("page_analysis_phase", "planner_phase") # Planner runs after page analysis
    
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
                            await websocket.send_text(f"AgentTool({phase_key}): {tool_name}({json.dumps(tool_args)})")
                            await asyncio.sleep(0.1) 
        
        elif role == "tool": # This is an observation/result from a tool
            tool_content = msg.get("content")
            # Ensure content is a string before stripping
            if isinstance(tool_content, str) and tool_content.strip():
                await websocket.send_text(f"AgentObs({phase_key}): {tool_content.strip()}")
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
