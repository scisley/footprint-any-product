import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import { writeFile } from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

const execPromise = promisify(exec);

export async function POST(request: Request) {
  try {
    // Get data from request body
    const runsData = await request.json();
    
    if (!runsData || !Array.isArray(runsData)) {
      return NextResponse.json({ error: 'Request body must be an array of run objects' }, { status: 400 });
    }
    
    // Save the data to a temporary JSON file (to avoid command line escape issues)
    const tempFilePath = path.join(os.tmpdir(), `muir_runs_${Date.now()}.json`);
    await writeFile(tempFilePath, JSON.stringify(runsData));
    
    // Execute the Python script to create runs
    const { stdout, stderr } = await execPromise(`python3 ../../../../frontend/muir_api_client.py create_runs ${tempFilePath}`);
    
    if (stderr) {
      console.error('Error from Python script:', stderr);
      return NextResponse.json({ error: stderr }, { status: 500 });
    }
    
    // Parse the output to extract JSON data
    let jsonDataString = '';
    const outputLines = stdout.split('\n');
    let captureJson = false;
    
    for (const line of outputLines) {
      if (line.includes('Create Runs Response:')) {
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