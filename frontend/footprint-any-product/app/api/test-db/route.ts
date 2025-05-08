import { NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';

export async function GET() {
  try {
    // Debug: Check if we have a database connection URL
    const connectionString = process.env.NEON_DATABASE_URL || '';
    console.log('NEON DB Connection String available:', !!connectionString);
    
    // Add fallback database URL for development
    const fallbackUrl = 'postgresql://neondb_owner:npg_nxcyN9hG1RZK@ep-spring-king-a6cy1uq1-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require';
    const url = connectionString || fallbackUrl;
    
    // Initialize Neon client
    const sql = neon(url);
    
    // Test the connection
    const testResult = await sql`SELECT 1 as test`;
    
    // Check if tables exist
    const tablesResult = await sql`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public'
    `;
    
    interface TableRow {
      table_name: string;
      [key: string]: unknown;
    }
    
    // Use type assertion to tell TypeScript about the real shape of the data
    const tables = (tablesResult as TableRow[]).map(row => row.table_name);
    
    // Count rows in analysis_results table if it exists
    let rowCount = 0;
    if (tables.includes('analysis_results')) {
      const countResult = await sql`SELECT COUNT(*) as count FROM analysis_results`;
      rowCount = countResult[0].count;
    }
    
    return NextResponse.json({
      connection: 'success',
      test: testResult,
      tables,
      'analysis_results_count': rowCount
    });
  } catch (error) {
    console.error('Error testing database connection:', error);
    return NextResponse.json(
      { 
        connection: 'failed',
        error: error instanceof Error ? error.message : 'Unknown error' 
      },
      { status: 500 }
    );
  }
}