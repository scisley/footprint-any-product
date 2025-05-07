import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';

const execPromise = promisify(exec);

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const page = searchParams.get('page') || '0';
    const perPage = searchParams.get('per_page') || '30';
    
    // Execute the Python script to get all runs
    const { stdout, stderr } = await execPromise(`python3 ../../../../frontend/muir_api_client.py get_all_runs ${page} ${perPage}`);
    
    if (stderr) {
      console.error('Error from Python script:', stderr);
      return NextResponse.json({ error: stderr }, { status: 500 });
    }
    
    // Parse the output to extract JSON data
    let jsonDataString = '';
    const outputLines = stdout.split('\n');
    let captureJson = false;
    
    for (const line of outputLines) {
      if (line.includes('All Carbon Runs:')) {
        captureJson = true;
        continue;
      }
      
      if (captureJson && !line.includes('... and') && !line.includes('---')) {
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