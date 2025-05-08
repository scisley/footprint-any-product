import { NextRequest, NextResponse } from 'next/server';
import type { 
  MaterialsAgentOutput,
  ManufacturingAgentOutput,
  PackagingAgentOutput,
  TransportAgentOutput,
  LifecycleAgentOutput,
  EndOfLifeAgentOutput,
  SummaryAgentOutput
} from '../../lib/agent-types';
import { sendMessage } from '../websocket/route';

// No mock response generation - we NEVER use mock data

/**
 * API route for making LLM agent calls
 * 
 * This route allows secure LLM calls from the client, with
 * proper API key handling on the server side.
 */
export async function POST(req: NextRequest) {
  try {
    // Parse request body
    const body = await req.json();
    const { agent, productInfo } = body;
    
    // Get the session ID from the request headers
    const sessionId = req.headers.get('X-Session-ID');
    
    if (!agent || !productInfo) {
      return NextResponse.json(
        { error: 'Missing required fields: agent and productInfo' },
        { status: 400 }
      );
    }
    
    // Validate agent name
    const validAgents = [
      'MaterialsAgent',
      'ManufacturingAgent',
      'PackagingAgent',
      'TransportAgent',
      'LifecycleAgent',
      'EndOfLifeAgent',
      'SummaryAgent'
    ];
    
    if (!validAgents.includes(agent)) {
      return NextResponse.json(
        { error: `Invalid agent name. Must be one of: ${validAgents.join(', ')}` },
        { status: 400 }
      );
    }
    
    // Use the real API key in this server-side environment
    const API_KEY = process.env.EXTERNAL_API_KEY || process.env.BAML_API_KEY;
    
    if (!API_KEY) {
      console.error("API_KEY is not set in environment variables");
      return NextResponse.json(
        { error: "API configuration error. Please check server logs." },
        { status: 500 }
      );
    }
    
    try {
      // Make the actual API call to the external API
      const apiUrl = process.env.EXTERNAL_API_URL || 'https://api.footprint-analyzer.com';
      const endpoint = `${apiUrl}/agents/${agent}`;
      // We always make real API calls
      
      console.log(`Making API call to: ${endpoint}`);
      
      // Send WebSocket update that we're starting the API call
      if (sessionId) {
        await sendMessage(sessionId, {
          type: 'agent_status_update',
          agent,
          status: 'processing',
          message: `Processing ${agent} analysis...`,
          timestamp: new Date().toISOString()
        });
      }
      
      let apiResponse;
      
      try {
        // Always make real API calls
        console.log(`[API REQUEST] Sending to ${endpoint}: ${JSON.stringify({ productInfo }, null, 2)}`);
        console.log(`[API REQUEST] Using API_KEY: ${API_KEY ? API_KEY.substring(0, 5) + '...' : 'undefined'}`);
        
        apiResponse = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${API_KEY}`,
            'Accept': 'application/json'
          },
          body: JSON.stringify({ productInfo }),
        });
        
        console.log(`[API RESPONSE] Status: ${apiResponse.status}`);
        
        if (apiResponse.ok) {
          const responseClone = apiResponse.clone();
          const responseBody = await responseClone.text();
          console.log(`[API RESPONSE] Body: ${responseBody}`);
        } else {
          console.error(`[API RESPONSE] Error: ${apiResponse.statusText}`);
        }
      } catch (error) {
        // We NEVER use mock data - always throw the error
        console.error(`[API CRITICAL ERROR] Failed to make API request:`, error);
        throw new Error(`API request failed: ${error instanceof Error ? error.message : String(error)}`);
      }
      
      if (!apiResponse.ok) {
        const errorData = await apiResponse.json().catch(() => ({}));
        console.error(`[API ERROR] Status: ${apiResponse.status}, Error data: ${JSON.stringify(errorData)}`);
        throw new Error(errorData.message || `API returned status: ${apiResponse.status}`);
      }
      
      const result = await apiResponse.json();
      
      // Send WebSocket update with success
      if (sessionId) {
        await sendMessage(sessionId, {
          type: 'agent_status_update',
          agent,
          status: 'completed',
          message: `Completed ${agent} analysis`,
          timestamp: new Date().toISOString()
        });
      }
      
      return NextResponse.json({ data: result }, {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*', // In production, restrict this to your domain
          'Cache-Control': 'no-store'
        }
      });
    } catch (error) {
      console.error(`[API ERROR] Error processing ${agent}:`, error);
      console.error(`[API ERROR] Stack trace: ${error instanceof Error ? error.stack : 'No stack trace'}`);
      
      // Log API_KEY status
      console.error(`[API ERROR] API Key check: ${API_KEY ? 'API key is set' : 'API key is missing'}`);
      
      // Send WebSocket update with error
      if (sessionId) {
        await sendMessage(sessionId, {
          type: 'agent_status_update',
          agent,
          status: 'error',
          message: `Error processing ${agent}: ${error instanceof Error ? error.message : String(error)}`,
          timestamp: new Date().toISOString()
        });
      }
      
      return NextResponse.json(
        { error: 'Failed to process agent request', details: error instanceof Error ? error.message : String(error) },
        { 
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        }
      );
    }
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : String(error) },
      { 
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    );
  }
}