import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const runId = params.id;
    
    if (!runId) {
      return NextResponse.json({ error: 'Run ID is required' }, { status: 400 });
    }
    
    // Get API key from environment variables
    const MUIR_API_KEY = process.env.MUIR_API_KEY;
    
    if (!MUIR_API_KEY) {
      console.error('MUIR_API_KEY is not set in environment variables');
      return NextResponse.json({ error: 'API configuration error. Please check server logs.' }, { status: 500 });
    }
    
    // Make direct API call to Muir API
    const apiUrl = 'https://service-run-api.muir.ai';
    const endpoint = `${apiUrl}/carbon_origin/runs/${runId}`;
    
    console.log(`Making API call to: ${endpoint}`);
    
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'APIKey': MUIR_API_KEY,
        'Accept': '*/*',
      }
    });
    
    if (!response.ok) {
      const errorMessage = `Error: ${response.status} ${response.statusText}`;
      let errorDetails;
      
      try {
        const errorData = await response.json();
        errorDetails = errorData.message || errorMessage;
      } catch {
        errorDetails = errorMessage;
      }
      
      console.error('Error from Muir API:', errorDetails);
      return NextResponse.json({ error: errorDetails }, { status: response.status });
    }
    
    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error) {
    console.error('Error calling Muir API:', error);
    return NextResponse.json({ 
      error: 'Failed to execute API request', 
      details: error instanceof Error ? error.message : String(error) 
    }, { status: 500 });
  }
}