'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import AgentCard from './components/AgentCard';
import SummaryCard from './components/SummaryCard';
// Import components

// Import shared types
import { Agent, ApiResponse } from './types';

// Import agents processing function
import { processProductAnalysis } from './lib/agents';

// Import WebSocket utilities
import { initSessionId, initWebSocketConnection, addMessageHandler, closeWebSocketConnection } from './lib/websocket';

export default function Home() {
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [apiResponse, setApiResponse] = useState<ApiResponse | null>(null);
  const [expandedAgentId, setExpandedAgentId] = useState<number | null>(null);
  const [showRawJson, setShowRawJson] = useState<boolean>(false);
  const [showHero, setShowHero] = useState<boolean>(true);
  
  // Initial agents state - in a real app, this might be empty or 'loading'
  const initialAgents: Agent[] = [
    { id: 1, name: 'Materials Agent', status: 'Idle', carbonScore: 0 },
    { id: 2, name: 'Manufacturing Agent', status: 'Idle', carbonScore: 0 },
    { id: 3, name: 'Packaging Agent', status: 'Idle', carbonScore: 0 },
    { id: 4, name: 'Transport Agent', status: 'Idle', carbonScore: 0 },
    { id: 5, name: 'Lifecycle Use Agent', status: 'Idle', carbonScore: 0 },
    { id: 6, name: 'End-of-Life Agent', status: 'Idle', carbonScore: 0 },
    { id: 7, name: 'Summary Agent', status: 'Idle', carbonScore: 0 }
  ];
  
  const [agents, setAgents] = useState<Agent[]>(initialAgents);
  
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
  
  // Initialize WebSocket connection when component mounts
  useEffect(() => {
    // Initialize the session ID
    initSessionId();
    
    // Initialize WebSocket connection
    initWebSocketConnection();
    
    // Set up message handler for WebSocket updates
    const removeHandler = addMessageHandler((message) => {
      if (message.type === 'agent_status_update') {
        // Find the agent with the matching name
        const agentIndex = agents.findIndex(agent => 
          agent.name.toLowerCase().includes(message.agent.toLowerCase().replace('Agent', ''))
        );
        
        if (agentIndex !== -1) {
          // Update the agent's status
          setAgents(prevAgents => 
            prevAgents.map((agent, index) => 
              index === agentIndex 
                ? { 
                    ...agent, 
                    status: message.status === 'processing' ? 'Processing...' : 
                            message.status === 'completed' ? 'Completed' : 
                            message.status === 'error' ? 'Error' : agent.status
                  } 
                : agent
            )
          );
        }
      }
    });
    
    // Clean up WebSocket connection on unmount
    return () => {
      removeHandler();
      closeWebSocketConnection();
    };
  }, []);
  
  const handleAnalyze = async () => {
    if (!url) return;
    
    // Hide hero section
    setShowHero(false);
    
    // Start the analysis
    setIsAnalyzing(true);
    
    try {
      // Reset agents to show "analyzing" state
      setAgents(prevAgents => 
        prevAgents.map(agent => ({ ...agent, status: 'Queued', carbonScore: 0 }))
      );
      
      // Update agent callback function
      const updateAgent = (agentId: number, updatedAgent: Partial<Agent>) => {
        setAgents(prevAgents => 
          prevAgents.map(agent => 
            agent.id === agentId 
              ? { ...agent, ...updatedAgent } 
              : agent
          )
        );
      };
      
      // Process all agents using BAML
      await processProductAnalysis(url, updateAgent);
      
      // Analysis complete
      setIsAnalyzing(false);
      
    } catch (error) {
      console.error("Error during analysis:", error);
      setIsAnalyzing(false);
    }
  };
  
  return (
    <div 
      className="min-h-screen p-6 pb-10"
      style={{ background: "var(--background)" }}
    >
      
      <header className="relative z-10 max-w-5xl mx-auto py-6 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 
              className="text-2xl md:text-3xl font-bold" 
              style={{ color: 'var(--primary)' }}
            >
              Carbon Footprint Analyzer
            </h1>
            <p className="mt-1" style={{ color: 'var(--foreground)' }}>
              Analyze the environmental impact of any product
            </p>
          </div>
          <div className="flex gap-2">
            <Link
              href="/muir"
              className="eco-button px-3 py-1.5 rounded inline-flex items-center text-sm"
              style={{ 
                backgroundColor: 'var(--primary)',
                color: 'white'
              }}
            >
              Muir API
            </Link>
            <Link
              href="/history"
              className="eco-button px-3 py-1.5 rounded inline-flex items-center text-sm"
              style={{ 
                backgroundColor: 'var(--button-hover)',
                border: '1px solid var(--card-border)',
                color: 'var(--foreground)'
              }}
            >
              View History
            </Link>
          </div>
        </div>
      </header>
      
      <div className="max-w-5xl mx-auto relative z-10">
        {/* Hero section - visible before analyzing */}
        {showHero && (
          <div 
            className="mb-10 flex flex-col items-center justify-center"
          >
            <div 
              className="text-center max-w-xl my-8 p-6 rounded-xl"
              style={{ 
                backgroundColor: 'var(--card-background)',
                borderWidth: '1px',
                borderColor: 'var(--card-border)',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
              }}
            >
              <h2 className="text-2xl font-bold mb-3" style={{ color: 'var(--primary)' }}>
                Discover Your Product&apos;s Environmental Impact
              </h2>
              <p className="mb-3 opacity-80">
                Enter a product URL to analyze its carbon footprint across materials, manufacturing, 
                packaging, transportation, usage, and end-of-life disposal.
              </p>
              <p className="text-sm font-medium" style={{ color: 'var(--primary-dark)' }}>
                Our AI agents will provide a comprehensive sustainability assessment.
              </p>
            </div>
          </div>
        )}
        
        {/* URL Input and Analyze Button */}
        <div className="mb-10">
          <div 
            className="flex flex-col sm:flex-row gap-2 p-4 rounded-xl shadow-md"
            style={{ 
              backgroundColor: 'var(--card-background)',
              border: '1px solid var(--card-border)',
            }}
          >
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter Product Name or URL (e.g., 'Apple MacBook Pro' or product URL)"
              className="flex-grow p-3 rounded-lg outline-glow focus:outline-none"
              style={{ 
                backgroundColor: 'var(--card-background)', 
                color: 'var(--foreground)',
                borderWidth: '1px',
                borderColor: 'var(--card-border)',
                borderStyle: 'solid'
              }}
              disabled={isAnalyzing}
            />
            <button
              onClick={handleAnalyze}
              disabled={!url || isAnalyzing}
              className="eco-button px-6 py-3 rounded-lg font-medium text-white flex items-center justify-center min-w-32"
              style={{ 
                backgroundColor: !url || isAnalyzing ? 'var(--score-neutral)' : 'var(--primary)',
                transition: 'all 0.2s',
              }}
            >
              {isAnalyzing ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing...
                </>
              ) : (
                'Analyze'
              )}
            </button>
          </div>
        </div>
        
        {/* Agent Sections - First 6 agents */}
        <div className="flex flex-col gap-4 mb-6">
          {agents.slice(0, 6).map((agent, index) => (
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
        
        {/* Summary Section */}
        <SummaryCard
          agent={agents[6]} // Summary Agent (id: 7)
          isExpanded={expandedAgentId === 7}
          showRawJson={showRawJson}
          onToggleDetails={() => toggleAgentDetails(7)}
          onToggleRawJson={() => toggleRawJson(7)}
        />
        
        {/* Footer */}
        <footer className="text-center mt-12 opacity-70 text-sm">
          <p>Carbon Footprint Analyzer - Hackathon Project 2025</p>
        </footer>
      </div>
    </div>
  );
}