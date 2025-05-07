import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';

const execPromise = promisify(exec);

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const procurementId = params.id;
    
    if (!procurementId) {
      return NextResponse.json({ error: 'Procurement ID is required' }, { status: 400 });
    }
    
    // Execute the Python script to get procurement run
    const { stdout, stderr } = await execPromise(`python3 ../../../../../frontend/muir_api_client.py get_procurement_run ${procurementId}`);
    
    if (stderr) {
      console.error('Error from Python script:', stderr);
      return NextResponse.json({ error: stderr }, { status: 500 });
    }
    
    // Parse the output to extract JSON data
    let jsonDataString = '';
    const outputLines = stdout.split('\n');
    let captureJson = false;
    
    for (const line of outputLines) {
      if (line.includes(`Carbon Run Details for Procurement ${procurementId}:`)) {
        captureJson = true;
        continue;
      }
      
      if (captureJson) {
        jsonDataString += line;
      }
    }
    
    try {
      const jsonData = JSON.parse(jsonDataString);
      return NextResponse.json(jsonData);
    } catch (parseError) {
      console.error('Error parsing JSON from script output:', parseError);
      return NextResponse.json({ 
        error: 'Failed to parse JSON from script output', 
        rawOutput: stdout 
      }, { status: 500 });
    }
  } catch (error) {
    console.error('Error executing Python script:', error);
    return NextResponse.json({ error: 'Failed to execute API request' }, { status: 500 });
  }
}