import { NextRequest } from 'next/server';

// This enables streaming for this API route
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const sessionId = searchParams.get('sessionId');
  
  if (!sessionId) {
    return new Response('No sessionId provided', { status: 400 });
  }
  
  // Create a TransformStream to manage the WebSocket connection
  const { readable, writable } = new TransformStream();
  const encoder = new TextEncoder();
  const writer = writable.getWriter();
  
  // Send an initial connection confirmation
  const initialMessage = {
    type: 'connection_established',
    sessionId,
    timestamp: new Date().toISOString()
  };
  
  await writer.write(encoder.encode(`data: ${JSON.stringify(initialMessage)}\n\n`));
  
  // Track this connection in global connections map
  // This allows other parts of the application to send messages to this client
  if (typeof global.connections === 'undefined') {
    global.connections = new Map();
  }
  
  global.connections.set(sessionId, writer);
  
  // Clean up when connection closes
  req.signal.addEventListener('abort', () => {
    if (global.connections && global.connections.has(sessionId)) {
      global.connections.delete(sessionId);
      console.log(`WebSocket connection closed for session: ${sessionId}`);
    }
  });
  
  return new Response(readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive'
    }
  });
}

// Helper function to send a message to a specific client
export async function sendMessage(sessionId: string, message: any) {
  try {
    if (!global.connections || !global.connections.has(sessionId)) {
      console.error(`No active connection for session: ${sessionId}`);
      return false;
    }
    
    const writer = global.connections.get(sessionId);
    const encoder = new TextEncoder();
    await writer.write(encoder.encode(`data: ${JSON.stringify(message)}\n\n`));
    return true;
  } catch (error) {
    console.error('Error sending WebSocket message:', error);
    return false;
  }
}

// Define global connections map type for TypeScript
declare global {
  // eslint-disable-next-line no-var
  var connections: Map<string, any>;
}