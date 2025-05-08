# WebSocket Streaming Test

This document provides instructions for testing the WebSocket-based streaming functionality using a simplified test server.

## Testing Setup

### 1. Create Environment Variables

First, make sure you have your environment variables set up. Create a `.env.local` file in the project root with:

```
OPENAI_API_KEY=your_openai_api_key
```

### 2. Run the Test WebSocket Server

```bash
python websocket_test.py
```

This will start a simple FastAPI server with a WebSocket endpoint on port 8000.

### 3. Start the Frontend

In another terminal, navigate to the frontend directory and start the Next.js development server:

```bash
cd frontend
pnpm dev --turbopack
```

### 4. Test the Connection

1. Open your browser to http://localhost:3000
2. Enter any product URL or name in the input field
3. Click "Analyze Carbon Footprint"
4. You should see messages streaming in from the server with simulated phase results

## How It Works

1. The `websocket_test.py` script:
   - Creates a WebSocket endpoint at `/ws`
   - Accepts connections and receives the product URL
   - Simulates processing by sending messages with delays
   - Sends phase results and a final summary

2. The frontend:
   - Connects to the WebSocket server
   - Sends the product URL/name
   - Displays the streaming messages with formatting

## Debugging

If you encounter issues:

1. Check the console in both the terminal running the WebSocket server and the browser developer tools
2. Ensure port 8000 is available and not blocked by a firewall
3. Verify the WebSocket URL in the frontend code matches the server address

Once the test is working, you can move on to integrating the real LangGraph streaming functionality.