'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
// Import components
import ResultsTable from '../components/history/ResultsTable';
import Pagination from '../components/history/Pagination';
import SearchFilters from '../components/history/SearchFilters';

// Import types from central location
import { HistoryResult, DebugInfo } from '../types';

export default function History() {
  const [results, setResults] = useState<HistoryResult[]>([]);
  const [filteredResults, setFilteredResults] = useState<HistoryResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [itemsPerPage] = useState<number>(10);
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  
  // Function to fetch results from the API that connects to NEON database
  const fetchResults = async () => {
    try {
      setIsLoading(true);
      
      // First test the database connection
      try {
        const testResponse = await fetch('/api/test-db');
        const testData = await testResponse.json();
        setDebugInfo(testData);
        console.log('Database test result:', testData);
      } catch (testError) {
        console.error('Database test error:', testError);
      }
      
      try {
        // Fetch results from our API
        const response = await fetch('/api/results');
        
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API results:', data);
        setResults(data);
        setFilteredResults(data);
      } catch (apiError) {
        console.error('API Error:', apiError);
        
        // Fallback to mock data if API fails or in development
        // This allows the UI to work without a real database connection
        const mockData: HistoryResult[] = [
          {
            id: "client-mock-1",
            product_url: "MOCK",
            timestamp: "2025-05-07T15:27:00Z",
            status: "MOCK",
            overall_score: 50,
            product_name: "MOCK"
          },
          {
            id: "client-mock-2",
            product_url: "MOCK",
            timestamp: "2025-05-06T10:15:30Z",
            status: "MOCK",
            overall_score: 42,
            product_name: "MOCK"
          },
          {
            id: "client-mock-3",
            product_url: "MOCK",
            timestamp: "2025-05-05T08:45:12Z",
            status: "MOCK",
            overall_score: 38,
            product_name: "MOCK"
          },
          {
            id: "client-mock-4",
            product_url: "MOCK",
            timestamp: "2025-05-04T14:22:18Z",
            status: "MOCK",
            overall_score: 63,
            product_name: "MOCK"
          },
          {
            id: "client-mock-5",
            product_url: "MOCK",
            timestamp: "2025-05-03T16:30:45Z",
            status: "MOCK",
            overall_score: 55,
            product_name: "MOCK"
          }
        ];
        
        setResults(mockData);
        setFilteredResults(mockData);
        console.log('Using mock data since API call failed');
      }
      
      setIsLoading(false);
      
    } catch (err) {
      setError('Failed to fetch results. Please try again later.');
      setIsLoading(false);
      console.error('Error fetching results:', err);
    }
  };
  
  useEffect(() => {
    fetchResults();
  }, []);
  
  // Pagination logic
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredResults.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredResults.length / itemsPerPage);
  
  const handlePageChange = (pageNumber: number) => {
    setCurrentPage(pageNumber);
  };
  
  // Search and filter functions
  const handleSearch = (searchTerm: string) => {
    if (!searchTerm.trim()) {
      setFilteredResults(results);
      setCurrentPage(1);
      return;
    }
    
    const searchLower = searchTerm.toLowerCase();
    const filtered = results.filter(result => 
      (result.product_name && result.product_name.toLowerCase().includes(searchLower)) ||
      result.product_url.toLowerCase().includes(searchLower)
    );
    
    setFilteredResults(filtered);
    setCurrentPage(1);
  };
  
  const handleScoreFilterChange = (minScore: number, maxScore: number) => {
    const filtered = results.filter(result => 
      result.overall_score >= minScore && result.overall_score <= maxScore
    );
    
    setFilteredResults(filtered);
    setCurrentPage(1);
  };
  
  const handleDateFilterChange = (startDate: string | null, endDate: string | null) => {
    if (!startDate && !endDate) {
      setFilteredResults(results);
      setCurrentPage(1);
      return;
    }
    
    const filtered = results.filter(result => {
      const resultDate = new Date(result.timestamp);
      
      if (startDate && endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        // Set end date to end of day
        end.setHours(23, 59, 59, 999);
        return resultDate >= start && resultDate <= end;
      } else if (startDate) {
        const start = new Date(startDate);
        return resultDate >= start;
      } else if (endDate) {
        const end = new Date(endDate);
        // Set end date to end of day
        end.setHours(23, 59, 59, 999);
        return resultDate <= end;
      }
      
      return true;
    });
    
    setFilteredResults(filtered);
    setCurrentPage(1);
  };
  
  
  return (
    <div 
      className="min-h-screen p-6 pb-10"
      style={{ background: "var(--background)" }}
    >
      <header className="relative z-10 max-w-5xl mx-auto py-6 mb-4">
        <div className="text-center">
          <h1 
            className="text-2xl md:text-3xl font-bold" 
            style={{ color: 'var(--primary)' }}
          >
            Previous Analysis Results
          </h1>
          <p className="mt-1" style={{ color: 'var(--foreground)' }}>
            View your product analysis history
          </p>
        </div>
      </header>
      
      <div className="max-w-5xl mx-auto relative z-10">
        {/* Navigation */}
        <div className="mb-8">
          <Link 
            href="/"
            className="eco-button inline-flex items-center px-4 py-2 rounded-lg font-medium"
            style={{ 
              backgroundColor: 'var(--primary)',
              color: 'white'
            }}
          >
            ← Back to Analyzer
          </Link>
        </div>
        
        {/* Search Filters */}
        <SearchFilters 
          onSearch={handleSearch}
          onScoreFilterChange={handleScoreFilterChange}
          onDateFilterChange={handleDateFilterChange}
        />
        
        {/* Results Table */}
        <div 
          className="p-4 rounded-xl shadow-md mb-8"
          style={{ 
            backgroundColor: 'var(--card-background)',
            border: '1px solid var(--card-border)',
          }}
        >
          <div className="flex justify-between items-center mb-4">
            <h2 
              className="text-xl font-bold"
              style={{ color: 'var(--foreground)' }}
            >
              Analysis History
            </h2>
            
            <div className="text-sm" style={{ color: 'var(--score-neutral)' }}>
              Showing {filteredResults.length > 0 ? indexOfFirstItem + 1 : 0}-
              {Math.min(indexOfLastItem, filteredResults.length)} of {filteredResults.length} results
            </div>
          </div>
          
          <ResultsTable 
            results={currentItems}
            isLoading={isLoading}
            error={error}
          />
          
          {/* Pagination */}
          {filteredResults.length > 0 && !isLoading && (
            <Pagination 
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          )}
        </div>
        
        {/* Debug Information (only visible during development) */}
        {debugInfo && (
          <div 
            className="p-4 rounded-xl shadow-md mb-8 mt-8"
            style={{ 
              backgroundColor: 'var(--card-background)',
              border: '1px solid var(--card-border)',
            }}
          >
            <h3 className="text-lg font-bold mb-2" style={{ color: 'var(--foreground)' }}>Database Connection Debug</h3>
            <pre 
              className="text-xs p-3 rounded overflow-auto max-h-80"
              style={{ 
                backgroundColor: 'rgba(0, 0, 0, 0.05)',
                color: 'var(--foreground)'
              }}
            >
              {JSON.stringify(debugInfo, null, 2)}
            </pre>
          </div>
        )}
        
        {/* Footer */}
        <footer className="text-center mt-12 opacity-70 text-sm">
          <p>Carbon Footprint Analyzer - Hackathon Project 2025</p>
        </footer>
      </div>
    </div>
  );
}