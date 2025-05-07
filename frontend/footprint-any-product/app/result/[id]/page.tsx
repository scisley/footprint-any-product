'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import AgentCard from '../../components/AgentCard';
import SummaryCard from '../../components/SummaryCard';
// Import components

// Import shared types
import { Agent, ApiResponse } from '../../types';

export default function ResultDetail() {
  const params = useParams();
  const resultId = params.id as string;
  
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedAgentId, setExpandedAgentId] = useState<number | null>(null);
  const [showRawJson, setShowRawJson] = useState<boolean>(false);
  
  // Function to fetch result details from the API that connects to NEON database
  const fetchResultDetail = useCallback(async () => {
    try {
      setIsLoading(true);
      
      try {
        // Fetch result details from our API
        const response = await fetch(`/api/results/${resultId}`);
        
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        
        const data = await response.json();
        setResult(data);
      } catch (apiError) {
        console.error('API Error:', apiError);
        
        // Fallback to mock data if API fails or in development
        // This allows the UI to work without a real database connection
        const mockResponse = await fetch('/mock-data.json');
        if (!mockResponse.ok) {
          throw new Error('Failed to load mock data');
        }
        
        const mockData: ApiResponse = await mockResponse.json();
        
        // Replace all text fields with "MOCK" to clearly indicate mock data
        const enhancedMockData = {
          ...mockData,
          product_name: "MOCK",
          product_url: "MOCK",
          status: "MOCK",
          agents: mockData.agents.map(agent => ({
            ...agent,
            name: "MOCK",
            status: "MOCK",
            details: "MOCK"
          }))
        };
        
        setResult(enhancedMockData);
        console.log('Using mock data since API call failed');
      }
      
      setIsLoading(false);
      
    } catch (err) {
      setError('Failed to fetch result details. Please try again later.');
      setIsLoading(false);
      console.error('Error fetching result details:', err);
    }
  }, [resultId]);
  
  useEffect(() => {
    fetchResultDetail();
  }, [fetchResultDetail]);
  
  // Toggle details for an agent
  const toggleAgentDetails = (agentId: number) => {
    if (expandedAgentId === agentId && !showRawJson) {
      setExpandedAgentId(null);
    } else {
      setExpandedAgentId(agentId);
      setShowRawJson(false);
    }
  };
  
  // Toggle raw JSON display
  const toggleRawJson = (agentId: number) => {
    if (expandedAgentId === agentId && showRawJson) {
      setShowRawJson(false);
    } else {
      setExpandedAgentId(agentId);
      setShowRawJson(true);
    }
  };
  
  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // Calculate overall carbon score
  const getOverallScore = (agents: Agent[]) => {
    if (!agents || agents.length === 0) return 0;
    const summaryAgent = agents.find(agent => agent.id === 7);
    return summaryAgent?.carbonScore || 0;
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
            Analysis Result
          </h1>
          <p className="mt-1" style={{ color: 'var(--foreground)' }}>
            Detailed product environmental impact assessment
          </p>
        </div>
      </header>
      
      <div className="max-w-5xl mx-auto relative z-10">
        {/* Navigation */}
        <div className="mb-8">
          <Link 
            href="/history"
            className="eco-button inline-flex items-center px-4 py-2 rounded-lg font-medium"
            style={{ 
              backgroundColor: 'var(--primary)',
              color: 'white'
            }}
          >
            ← Back to History
          </Link>
        </div>
        
        {isLoading ? (
          <div 
            className="p-8 rounded-xl shadow-md text-center"
            style={{ 
              backgroundColor: 'var(--card-background)',
              border: '1px solid var(--card-border)',
            }}
          >
            <div className="inline-block animate-spin mr-2">
              <svg className="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <span>Loading result details...</span>
          </div>
        ) : error ? (
          <div 
            className="p-8 rounded-xl shadow-md text-center"
            style={{ 
              backgroundColor: 'var(--card-background)',
              border: '1px solid var(--card-border)',
              color: 'var(--status-error)'
            }}
          >
            {error}
          </div>
        ) : result ? (
          <>
            {/* Result Overview */}
            <div 
              className="p-6 rounded-xl shadow-md mb-8"
              style={{ 
                backgroundColor: 'var(--card-background)',
                border: '1px solid var(--card-border)',
              }}
            >
              <h2 
                className="text-xl font-bold mb-4"
                style={{ color: 'var(--foreground)' }}
              >
                {result.product_name || 'Product Analysis'}
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <div className="text-sm font-medium mb-1" style={{ color: 'var(--score-neutral)' }}>
                    Product URL
                  </div>
                  <div className="break-all" style={{ color: 'var(--foreground)' }}>
                    <a 
                      href={result.product_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="hover:underline"
                      style={{ color: 'var(--primary)' }}
                    >
                      {result.product_url}
                    </a>
                  </div>
                </div>
                
                <div>
                  <div className="text-sm font-medium mb-1" style={{ color: 'var(--score-neutral)' }}>
                    Analysis Date
                  </div>
                  <div style={{ color: 'var(--foreground)' }}>
                    {formatDate(result.timestamp)}
                  </div>
                </div>
                
                <div>
                  <div className="text-sm font-medium mb-1" style={{ color: 'var(--score-neutral)' }}>
                    Overall Carbon Score
                  </div>
                  <div 
                    className="text-xl font-bold"
                    style={{ 
                      color: getOverallScore(result.agents) < 40 
                        ? 'var(--score-good)' 
                        : getOverallScore(result.agents) < 60 
                          ? 'var(--score-fair)' 
                          : 'var(--score-poor)'
                    }}
                  >
                    {getOverallScore(result.agents)}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Agent Cards */}
            <div className="flex flex-col gap-4 mb-6">
              {result.agents.slice(0, 6).map((agent, index) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  isExpanded={expandedAgentId === agent.id}
                  showRawJson={showRawJson}
                  onToggleDetails={() => toggleAgentDetails(agent.id)}
                  onToggleRawJson={() => toggleRawJson(agent.id)}
                  index={index}
                />
              ))}
            </div>
            
            {/* Summary Card */}
            <SummaryCard
              agent={result.agents[6]} // Summary Agent (id: 7)
              isExpanded={expandedAgentId === 7}
              showRawJson={showRawJson}
              onToggleDetails={() => toggleAgentDetails(7)}
              onToggleRawJson={() => toggleRawJson(7)}
            />
            
            {/* Json Download */}
            <div className="mt-8 text-center">
              <button
                onClick={() => {
                  const dataStr = JSON.stringify(result, null, 2);
                  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                  
                  const exportName = `carbon-analysis-${resultId}.json`;
                  
                  const linkElement = document.createElement('a');
                  linkElement.setAttribute('href', dataUri);
                  linkElement.setAttribute('download', exportName);
                  linkElement.click();
                }}
                className="eco-button px-4 py-2 rounded-lg inline-flex items-center"
                style={{ 
                  backgroundColor: 'var(--button-hover)',
                  border: '1px solid var(--card-border)',
                  color: 'var(--foreground)'
                }}
              >
                <svg className="w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download JSON Data
              </button>
            </div>
          </>
        ) : (
          <div 
            className="p-8 rounded-xl shadow-md text-center"
            style={{ 
              backgroundColor: 'var(--card-background)',
              border: '1px solid var(--card-border)',
            }}
          >
            No result found for ID: {resultId}
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