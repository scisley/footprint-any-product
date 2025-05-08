# WebSocket Streaming Integration

This document provides instructions for testing the WebSocket-based streaming functionality for real-time carbon footprint analysis.

## Overview

The system uses WebSockets to stream real-time analysis results from the LangGraph agents to the frontend. As each agent completes its analysis, results are immediately streamed to the user interface, providing a more interactive and engaging experience.

## Setup Instructions

### Environment Variables

1. Create a `.env.local` file in the project root with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   LANGCHAIN_API_KEY=your_langsmith_api_key  # Optional, for LangSmith tracing
   LANGCHAIN_PROJECT=footprint-any-product  # Optional, for naming your LangSmith project
   DB_DEV_CONNECTION=your_neon_db_connection_string  # If using DB persistence
   MUIR_API_KEY=your_muir_api_key  # If using Muir API
   ```

### Start the FastAPI Backend

1. Activate your virtual environment:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Start the FastAPI server with the WebSocket endpoint:
   ```bash
   fastapi dev main.py
   ```

3. The server will start on `http://localhost:8000` with the WebSocket endpoint available at `ws://localhost:8000/ws`.

### Start the Next.js Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies (if not already done):
   ```bash
   pnpm install
   ```

3. Start the development server:
   ```bash
   pnpm dev --turbopack
   ```

4. The frontend will be available at `http://localhost:3000`.

## Testing the Connection

1. Open the frontend application in your browser at `http://localhost:3000`.

2. Enter a product URL or name in the input field and click "Analyze Carbon Footprint".

3. The application will establish a WebSocket connection to the backend and begin streaming the analysis results.

4. You should see real-time updates as each phase of the analysis completes, with formatted output displaying:
   - Individual phase results (manufacturing, packaging, transportation, use, end-of-life)
   - A final summary with the total carbon footprint

## Troubleshooting

If you encounter issues with the WebSocket connection:

1. Verify that both servers are running correctly.

2. Check the browser console for any connection errors.

3. Ensure that port 8000 is not blocked by a firewall or used by another application.

4. If using a different port for the FastAPI server, update the WebSocket URL in the frontend code at `src/app/page.tsx` (change the `webSocketUrl` state value).

## Implementation Details

- The WebSocket endpoint is defined in `main.py` in the root directory.
- The frontend WebSocket client is implemented in `src/components/StreamingText.tsx`.
- The LangGraph streaming implementation uses the `stream` method with the `["updates", "values"]` modes to provide real-time updates.