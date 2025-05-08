import { NextRequest, NextResponse } from 'next/server';
import { getResultById } from '../../../lib/db';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const id = params.id;
    
    const result = await getResultById(id);
    
    if (!result) {
      return NextResponse.json(
        { error: 'Result not found' },
        { status: 404 }
      );
    }
    
    return NextResponse.json(result);
  } catch (error) {
    console.error('Error fetching result details from NEON database:', error);
    return NextResponse.json(
      { error: 'Failed to fetch result details' },
      { status: 500 }
    );
  }
}