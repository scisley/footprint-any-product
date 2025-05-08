# Data Flow: Agents to Frontend

This document describes the complete data flow from LangGraph agents through the backend WebSocket to the frontend streaming component.

## Overview

The Footprint-Any-Product system uses a multi-agent architecture powered by LangGraph to analyze different aspects of a product's lifecycle. The real-time results from these agents flow through WebSockets to provide a streaming user experience.

```
Agents (LangGraph) → Backend (FastAPI) → WebSocket → Frontend (Next.js) → StreamingText Component
```

## 1. Agent Layer

### Agent Structure

Each specialized agent follows the same pattern:

1. Takes input from the shared `FootprintState`
2. Processes it with tools (emissions_factor_finder_tool, calculator)
3. Returns structured data in a consistent format

Example from `eol.py`:
```python
async def eol_phase(state: FootprintState):
    input = f"""Brand: {state["brand"]}\nCategory: {state["category"]}\nDescription: {state["description"]}"""
    response = await eol_agent.ainvoke({
        "messages": [{"role": "user", "content": input}]
    })
    
    # Create the result with standardized structure
    result = {
        "eol": {
            "carbon": response["structured_response"].carbon, 
            "summary": response["structured_response"].summary, 
            "messages": response["messages"] + [
                {"role": "ai", "content": "Processing end-of-life information for this product..."},
                {"role": "ai", "content": "Evaluating recycling and disposal options..."},
                {"role": "ai", "content": f"Calculated total end-of-life carbon impact: {response['structured_response'].carbon} kg CO2e"}
            ]
        }
    }
    return result
```

### Message Types

Agent messages follow these patterns:

1. **ReAct Format Messages**: LLM reasoning steps with "Thought:", "Action:", "Observation:" prefixes
2. **Tool Calls**: Function invocations like `emissions_factor_finder_tool("recycling of cellphone")`
3. **Structured Response**: The final carbon estimation and summary

## 2. Backend Layer (main.py)

### LangGraph Management

1. **Graph Setup**: Creates a directed graph of agents (`manufacturing_phase`, `packaging_phase`, etc.)
2. **State Management**: Uses the `FootprintState` TypedDict to share data between nodes
3. **Stream Generation**: Creates an async stream with both updates and full state values
   ```python
   stream = graph.astream(
       initial_state,
       config,
       stream_mode=["updates", "values"]
   )
   ```

### Message Processing

The backend processes both types of LangGraph events:

1. **Updates Mode**: Contains incremental changes to state 
2. **Values Mode**: Contains the complete current state

For each update, the backend extracts agent data and transforms it into standardized formats:

```python
# Main message types
"PhaseStart: {phase_key}"
"Agent({phase_key}): {thought_content}" 
"AgentAction({phase_key}): {action_description}"
"AgentTool({phase_key}): {tool_name}({tool_args})"
"AgentObs({phase_key}): {observation_content}"
"PhaseSummary({phase_key}): {summary}"
"AgentStatus({phase_key}): {status}"
"SystemMessage: {content}"
"FinalSummary: {content}" 
"CarbonFootprint: {value}"
"AnalysisComplete"
"ErrorMessage: {error}"
```

### Message Extraction

The backend parses the complex ReAct format from LLMs:

```python
# Extract thoughts
if "Thought:" in content:
    thought_pattern = r"Thought:\s*(.*?)(?=\n[A-Za-z]+:|$)"
    thought_matches = re.findall(thought_pattern, content, re.DOTALL)
    
    for thought in thought_matches:
        thought_text = thought.strip()
        if len(thought_text) > 10:
            await websocket.send_text(f"Agent({phase_key}): {thought_text}")
```

## 3. WebSocket Layer

The WebSocket serves as the real-time communication channel between backend and frontend:

1. Client connects to `/ws` endpoint
2. Client sends product URL to analyze
3. Server streams standardized messages to client
4. Connection remains open until analysis completes

## 4. Frontend Layer (StreamingText.tsx)

### WebSocket Connection

```tsx
useEffect(() => {
  if (!isStreaming || !productUrl) return;
  
  const socket = new WebSocket(url);
  wsRef.current = socket;

  socket.onopen = () => {
    // Send request to start analysis
    const payload = JSON.stringify({ url: productUrl });
    socket.send(payload);
  };

  socket.onmessage = (event) => {
    // Process incoming messages
    const message = event.data;
    setText((prev) => prev + message + "\n");
  };
}, [isStreaming, url, productUrl]);
```

### Message Parsing

The frontend detects message types via pattern matching:

```tsx
if (message.startsWith('Agent(')) {
  const agentMatch = message.match(/^Agent\(([^)]+)\):/);
  const agentName = agentMatch ? agentMatch[1] : "unknown";
  const content = message.substring(message.indexOf(':') + 1).trim();
}
```

### Visual Formatting

Each message type gets specialized formatting:

```tsx
// For agent thoughts
return (
  <div className={`pl-4 my-1.5 border-l-2 ${borderColorClass}`}>
    <span className={`text-xs ${textColorClass} font-medium mr-2`}>
      <span className="mr-1">{agentIcon}</span>
      {agentName}:
    </span>
    {message}
  </div>
);

// For tool usage  
return (
  <div className="pl-4 my-1 border-l-2 border-blue-200 text-xs font-mono">
    <span className="text-blue-600">
      {agentName} using {toolName}
    </span>
    <span className="opacity-75"> with args: {toolArgs}</span>
  </div>
);
```

## 5. Rendering Order Issues

The streaming messages may sometimes appear out of order due to:

1. **Async Processing**: Agents run in parallel through LangGraph
2. **Variable Processing Time**: Different agents take different amounts of time
3. **Network Jitter**: WebSocket messages can arrive with slight timing variations

To improve the ordering:

1. Group messages by phase
2. Add timestamps to messages
3. Sort messages within a phase by timestamp
4. Add visual separation between phases

## Data Flow Sequence Diagram

```
┌──────────┐     ┌─────────┐     ┌──────────┐     ┌──────────────────┐
│  Agents  │     │ Backend │     │ WebSocket│     │ StreamingText    │
└────┬─────┘     └────┬────┘     └────┬─────┘     └────────┬─────────┘
     │                │                │                    │
     │ Process Data   │                │                    │
     │───────────────>│                │                    │
     │                │                │                    │
     │                │ Stream Updates │                    │
     │                │───────────────>│                    │
     │                │                │                    │
     │                │                │ Forward Messages   │
     │                │                │──────────────────>│
     │                │                │                    │ Parse & Format
     │                │                │                    │──────────────┐
     │                │                │                    │              │
     │                │                │                    │<─────────────┘
     │                │                │                    │ Render to UI
     │                │                │                    │──────────────┐
     │                │                │                    │              │
     │                │                │                    │<─────────────┘
     │                │                │                    │
```

## Message Format Reference

| Message Type | Format | Example |
|--------------|--------|---------|
| Agent Thought | `Agent({phase}): {content}` | `Agent(eol): I need to determine the recycling potential of this product` |
| Agent Action | `AgentAction({phase}): {action}` | `AgentAction(eol): I'll search for end-of-life options` |
| Tool Usage | `AgentTool({phase}): {tool}({args})` | `AgentTool(eol): emissions_factor_finder_tool("recycling of cellphone")` |
| Tool Result | `AgentObs({phase}): {observation}` | `AgentObs(eol): Found emissions factor of 0.5 kg CO2e per cellphone` |
| Agent Status | `AgentStatus({phase}): {status}` | `AgentStatus(eol): Carbon estimate: 0.75 kg CO2e` |
| Phase Start | `PhaseStart: {phase}` | `PhaseStart: manufacturing` |
| Phase Summary | `PhaseSummary({phase}): {summary}` | `PhaseSummary(eol): End-of-life emissions include recycling (0.5)...` |
| Final Summary | `FinalSummary: {content}` | `FinalSummary: Total carbon footprint: 9.76 kg CO2e` |
| Carbon Value | `CarbonFootprint: {value}` | `CarbonFootprint: 9.76` |
| System Message | `SystemMessage: {content}` | `SystemMessage: Processing eol phase with 8 messages` |
| Analysis Complete | `AnalysisComplete` | `AnalysisComplete` |