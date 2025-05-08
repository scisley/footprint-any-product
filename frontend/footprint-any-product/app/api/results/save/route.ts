import { NextRequest, NextResponse } from 'next/server';
import { saveAnalysisResult } from '../../../lib/db';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate the request body
    if (!body || !body.product_url || !body.overall_score || !Array.isArray(body.agents)) {
      return NextResponse.json(
        { error: 'Invalid request body. Missing required fields.' },
        { status: 400 }
      );
    }
    
    // Save the analysis result and get the new ID
    const resultId = await saveAnalysisResult(body);
    
    return NextResponse.json({ 
      message: 'Analysis result saved successfully',
      resultId 
    });
  } catch (error) {
    console.error('Error saving analysis result:', error);
    return NextResponse.json(
      { error: 'Failed to save analysis result' },
      { status: 500 }
    );
  }
}