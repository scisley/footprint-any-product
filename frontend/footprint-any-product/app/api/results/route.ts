import { NextResponse } from 'next/server';
import { getAllResults } from '../../lib/db';

export async function GET() {
  try {
    // Debug: Check if we have a database connection URL
    console.log('Database URL available:', !!process.env.NEON_DATABASE_URL);
    
    const results = await getAllResults();
    
    // Debug: Log results count
    console.log('Results fetched from database:', results.length);
    
    // If we have no results from the database, return mock data to ensure UI works
    if (!results || results.length === 0) {
      console.log('Returning mock data since database returned no results');
      
      const mockData = [
        {
          id: "mock-1",
          product_url: "MOCK",
          timestamp: "2025-05-07T15:27:00Z",
          status: "MOCK",
          overall_score: 50,
          product_name: "MOCK"
        },
        {
          id: "mock-2",
          product_url: "MOCK",
          timestamp: "2025-05-06T10:15:30Z",
          status: "MOCK",
          overall_score: 42,
          product_name: "MOCK"
        }
      ];
      
      return NextResponse.json(mockData);
    }
    
    return NextResponse.json(results);
  } catch (error) {
    console.error('Error fetching results from NEON database:', error);
    
    // Return mock data in case of error to ensure UI still works
    console.log('Returning mock data due to error');
    const mockData = [
      {
        id: "error-mock-1",
        product_url: "MOCK",
        timestamp: "2025-05-07T15:27:00Z",
        status: "MOCK",
        overall_score: 50,
        product_name: "MOCK"
      }
    ];
    
    return NextResponse.json(mockData);
  }
}