import { NextResponse } from 'next/server';
import { getAllResults } from '../../lib/db';

export async function GET() {
  try {
    // Debug: Check if we have a database connection URL
    console.log('Database URL available:', !!process.env.NEON_DATABASE_URL);
    
    const results = await getAllResults();
    
    // Debug: Log results count
    console.log('Results fetched from database:', results ? results.length : 0);
    
    // If we have no results from the database, return an empty array
    if (!results || results.length === 0) {
      console.log('No results found in database');
      return NextResponse.json([]);
    }
    
    return NextResponse.json(results);
  } catch (error) {
    console.error('Error fetching results from database:', error);
    
    // Return error response
    return NextResponse.json(
      { error: 'Failed to fetch results', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}