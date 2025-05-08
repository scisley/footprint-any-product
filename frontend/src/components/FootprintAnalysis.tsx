'use client';

import { useEffect, useRef, useState } from 'react';
import { FootprintAnalysisProps, AgentData } from '@/types/components';
import { AgentSection } from './AgentSection';

export function FootprintAnalysis({
  url = 'ws://localhost:3005/ws', // WebSocket URL
  isStreaming,
  productUrl, // Product URL
  onStreamingComplete
}: FootprintAnalysisProps) {
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [finalSummary, setFinalSummary] = useState<string>('');
  const [totalCarbonFootprint, setTotalCarbonFootprint] = useState<number | null>(null);
  const [agents, setAgents] = useState<Record<string, AgentData>>({
    planner: { messages: [], summary: '', carbon: null, isCompleted: false },
    materials: { messages: [], summary: '', carbon: null, isCompleted: false },
    manufacturing: { messages: [], summary: '', carbon: null, isCompleted: false },
    packaging: { messages: [], summary: '', carbon: null, isCompleted: false },
    transportation: { messages: [], summary: '', carbon: null, isCompleted: false },
    use: { messages: [], summary: '', carbon: null, isCompleted: false },
    eol: { messages: [], summary: '', carbon: null, isCompleted: false },
  });
  
  const wsRef = useRef<WebSocket | null>(null);
  const hasInitializedRef = useRef(false);

  useEffect(() => {
    // Only connect when streaming should start and we have the product URL
    if (!isStreaming || !productUrl) {
      // If streaming is intended but URL is missing, optionally log or set an error
      if (isStreaming) {
        console.warn('[FootprintAnalysis useEffect] Streaming is true, but product URL is missing. WebSocket will not connect.', { productUrl });
        // setError("Product URL is missing, cannot start analysis.");
      }
      return;
    }
    
    if (!wsRef.current) {
      // Set connecting state immediately when attempting to connect
      setIsConnecting(true);
      try {
        const socket = new WebSocket(url);
        wsRef.current = socket;

        socket.onopen = () => {
          setIsConnected(true);
          setIsConnecting(false);
          setError(null);
          // Reset state when starting a new analysis
          setFinalSummary('');
          setTotalCarbonFootprint(null);
          setAgents({
            planner: { messages: [], summary: '', carbon: null, isCompleted: false },
            materials: { messages: [], summary: '', carbon: null, isCompleted: false },
            manufacturing: { messages: [], summary: '', carbon: null, isCompleted: false },
            packaging: { messages: [], summary: '', carbon: null, isCompleted: false },
            transportation: { messages: [], summary: '', carbon: null, isCompleted: false },
            use: { messages: [], summary: '', carbon: null, isCompleted: false },
            eol: { messages: [], summary: '', carbon: null, isCompleted: false },
          });
          hasInitializedRef.current = true; // Mark that we've initialized a connection attempt
          
          // Send the product URL to the server immediately when the connection is established
          const payload = JSON.stringify({ url: productUrl });
          socket.send(payload);
          console.log('[FootprintAnalysis WebSocket] Sent payload:', payload);
        };

        socket.onmessage = (event) => {
          const message = event.data;
          console.log('[WebSocket] Message received:', message);
          
          // When we receive the first message, we know the connection is established
          if (message === "SystemMessage: WebSocket connection established") {
            setIsConnected(true);
            setIsConnecting(false);
            return;
          }
          
          if (message.startsWith('Agent(')) {
            // Process agent thinking
            try {
              const agentMatch = message.match(/^Agent\(([^)]+)\):/);
              if (agentMatch) {
                const agentName = agentMatch[1];
                const content = message.substring(message.indexOf(':') + 1).trim();
                
                setAgents(prev => {
                  // Make sure we have an entry for this agent
                  const agentData = prev[agentName] || { messages: [], summary: '', carbon: null, isCompleted: false };
                  
                  return {
                    ...prev,
                    [agentName]: {
                      ...agentData,
                      messages: [...agentData.messages, { type: 'thinking', content }],
                    }
                  };
                });
              }
            } catch (err) {
              console.error('[Agent Message Parse Error]:', err);
            }
          } else if (message.startsWith('AgentAction(')) {
            // Process agent actions
            try {
              const agentMatch = message.match(/^AgentAction\(([^)]+)\):/);
              if (agentMatch) {
                const agentName = agentMatch[1];
                const action = message.substring(message.indexOf(':') + 1).trim();
                
                setAgents(prev => {
                  const agentData = prev[agentName] || { messages: [], summary: '', carbon: null, isCompleted: false };
                  return {
                    ...prev,
                    [agentName]: {
                      ...agentData,
                      messages: [...agentData.messages, { type: 'action', content: action }],
                    }
                  };
                });
              }
            } catch (err) {
              console.error('[Agent Action Parse Error]:', err);
            }
          } else if (message.startsWith('AgentTool(')) {
            // Process agent tool calls
            try {
              const agentMatch = message.match(/^AgentTool\(([^)]+)\):\s*(\w+)\((.*)\)/);
              if (agentMatch) {
                const agentName = agentMatch[1];
                const toolName = agentMatch[2];
                const toolArgs = agentMatch[3];
                
                setAgents(prev => {
                  const agentData = prev[agentName] || { messages: [], summary: '', carbon: null, isCompleted: false };
                  return {
                    ...prev,
                    [agentName]: {
                      ...agentData,
                      messages: [...agentData.messages, { 
                        type: 'tool', 
                        content: `${toolName}(${toolArgs})` 
                      }],
                    }
                  };
                });
              }
            } catch (err) {
              console.error('[Agent Tool Parse Error]:', err);
            }
          } else if (message.startsWith('AgentObs(')) {
            // Process agent observations
            try {
              const agentMatch = message.match(/^AgentObs\(([^)]+)\):/);
              if (agentMatch) {
                const agentName = agentMatch[1];
                const observation = message.substring(message.indexOf(':') + 1).trim();
                
                setAgents(prev => {
                  const agentData = prev[agentName] || { messages: [], summary: '', carbon: null, isCompleted: false };
                  return {
                    ...prev,
                    [agentName]: {
                      ...agentData,
                      messages: [...agentData.messages, { type: 'observation', content: observation }],
                    }
                  };
                });
              }
            } catch (err) {
              console.error('[Agent Observation Parse Error]:', err);
            }
          } else if (message.startsWith('PhaseSummary(')) {
            // Process phase summary
            try {
              const phaseMatch = message.match(/^PhaseSummary\(([^)]+)\):\s*(.*)/);
              if (phaseMatch) {
                const phaseName = phaseMatch[1];
                const summary = phaseMatch[2];
                
                setAgents(prev => {
                  const agentData = prev[phaseName] || { messages: [], summary: '', carbon: null, isCompleted: false };
                  return {
                    ...prev,
                    [phaseName]: {
                      ...agentData,
                      summary,
                      isCompleted: true,
                    }
                  };
                });
              }
            } catch (err) {
              console.error('[Phase Summary Parse Error]:', err);
            }
          } else if (message.startsWith('PhaseCarbon(')) {
            // Process phase carbon
            try {
              const carbonMatch = message.match(/^PhaseCarbon\(([^)]+)\):\s*([\d.]+)/);
              if (carbonMatch) {
                const phaseName = carbonMatch[1];
                const carbon = parseFloat(carbonMatch[2]);
                
                if (!isNaN(carbon)) {
                  setAgents(prev => {
                    const agentData = prev[phaseName] || { messages: [], summary: '', carbon: null, isCompleted: false };
                    return {
                      ...prev,
                      [phaseName]: {
                        ...agentData,
                        carbon,
                      }
                    };
                  });
                }
              }
            } catch (err) {
              console.error('[Phase Carbon Parse Error]:', err);
            }
          } else if (message.startsWith('FinalSummary:')) {
            // Process final summary
            const summary = message.substring(13).trim();
            setFinalSummary(summary);
          } else if (message.startsWith('CarbonFootprint:')) {
            // Process total carbon footprint
            try {
              const carbonValue = message.substring(16).trim();
              const carbon = parseFloat(carbonValue);
              if (!isNaN(carbon)) {
                setTotalCarbonFootprint(carbon);
              }
            } catch (err) {
              console.error('[Carbon Footprint Parse Error]:', err);
            }
          } else if (message === "AnalysisComplete") {
            console.log('[Analysis Complete]');
            onStreamingComplete?.();
          }
        };

        socket.onclose = () => {
          setIsConnected(false);
          if (hasInitializedRef.current) {
            onStreamingComplete?.();
          }
        };

        socket.onerror = (err) => {
          setError('Failed to connect to server. Please try again later.');
          setIsConnecting(false);
          console.error('WebSocket error:', err);
        };
      } catch (err) {
        setError('Failed to connect to server. Please try again later.');
        setIsConnecting(false);
        console.error('WebSocket connection error:', err);
      }
    }

    // Cleanup on unmount or when streaming stops
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
        setIsConnected(false);
        setIsConnecting(false);
      }
    };
  }, [isStreaming, url, productUrl, onStreamingComplete]);

  // Render messages for an agent
  const renderAgentMessages = (agentMessages: Array<{type: string, content: string}>) => {
    return agentMessages.map((msg, index) => {
      if (msg.type === 'thinking') {
        return (
          <div key={index} className="pl-4 my-1.5 border-l-2 border-gray-300 text-gray-800 dark:text-gray-300 py-1">
            {msg.content}
          </div>
        );
      } else if (msg.type === 'action') {
        return (
          <div key={index} className="pl-4 my-1 border-l-2 border-gray-300 text-gray-600 dark:text-gray-400 text-sm italic">
            <span className="text-xs font-medium mr-2">Action:</span>
            {msg.content}
          </div>
        );
      } else if (msg.type === 'tool') {
        return (
          <div key={index} className="pl-4 my-1 border-l-2 border-blue-200 text-gray-600 dark:text-gray-400 text-xs font-mono">
            <span className="text-blue-600 dark:text-blue-400">Using tool:</span>
            <span className="opacity-75"> {msg.content}</span>
          </div>
        );
      } else if (msg.type === 'observation') {
        return (
          <div key={index} className="pl-4 my-1 border-l-2 border-gray-200 text-gray-500 dark:text-gray-400 text-xs">
            <span className="opacity-75">Observation:</span> {msg.content}
          </div>
        );
      }
      return <div key={index}>{msg.content}</div>;
    });
  };

  // Set up agent section styling configs
  const agentConfigs = {
    planner: {
      title: "Planning & Setup",
      bgColor: "bg-slate-50 dark:bg-slate-900/30", // Using slate for a neutral planning color
      textColor: "text-slate-800 dark:text-slate-200",
      borderColor: "border-slate-200"
    },
    materials: {
      title: "Materials",
      bgColor: "bg-rose-50 dark:bg-rose-900/30",
      textColor: "text-rose-800 dark:text-rose-200",
      borderColor: "border-rose-200"
    },
    manufacturing: {
      title: "Manufacturing",
      bgColor: "bg-blue-50 dark:bg-blue-900/30",
      textColor: "text-blue-800 dark:text-blue-200",
      borderColor: "border-blue-200"
    },
    packaging: {
      title: "Packaging",
      bgColor: "bg-amber-50 dark:bg-amber-900/30",
      textColor: "text-amber-800 dark:text-amber-200",
      borderColor: "border-amber-200"
    },
    transportation: {
      title: "Transportation",
      bgColor: "bg-indigo-50 dark:bg-indigo-900/30",
      textColor: "text-indigo-800 dark:text-indigo-200",
      borderColor: "border-indigo-200"
    },
    use: {
      title: "Product Use",
      bgColor: "bg-green-50 dark:bg-green-900/30",
      textColor: "text-green-800 dark:text-green-200",
      borderColor: "border-green-200"
    },
    eol: {
      title: "End of Life",
      bgColor: "bg-purple-50 dark:bg-purple-900/30",
      textColor: "text-purple-800 dark:text-purple-200",
      borderColor: "border-purple-200"
    }
  };

  // Agent execution order
  const agentOrder = ["planner", "materials", "manufacturing", "packaging", "transportation", "use", "eol"];

  // Show nothing if we're not streaming and have no data
  if (!isStreaming && !isConnecting && !Object.values(agents).some(agent => agent.messages.length > 0)) {
    return null;
  }

  return (
    <div className="w-full max-w-3xl mx-auto mt-8">
      <div className="rounded-lg border border-[var(--border)] bg-white dark:bg-gray-900 p-4 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium">Carbon Footprint Analysis</h3>
          {isConnecting && !isConnected && (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-yellow-500 animate-pulse"></div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Connecting to server...</span>
            </div>
          )}
          {isConnected && (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Generating analysis...</span>
            </div>
          )}
        </div>
        
        {error ? (
          <div className="text-red-500 p-4">{error}</div>
        ) : isConnecting && !isConnected && !Object.values(agents).some(agent => agent.messages.length > 0) ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin h-8 w-8 border-4 border-gray-200 border-t-[var(--primary)] rounded-full mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Establishing connection and preparing analysis...</p>
            <p className="text-xs text-gray-500 mt-2">This may take a few seconds</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Agent sections */}
            {agentOrder.map(agentKey => {
              const agent = agents[agentKey];
              const config = agentConfigs[agentKey as keyof typeof agentConfigs];
              const isActive = agent.messages.length > 0 || !!agent.summary;
              
              return (
                <AgentSection
                  key={agentKey}
                  agentKey={agentKey}
                  title={config.title}
                  summary={agent.summary}
                  content={renderAgentMessages(agent.messages)}
                  isCompleted={agent.isCompleted}
                  carbon={agent.carbon || undefined}
                  bgColor={isActive ? config.bgColor : "bg-gray-100 dark:bg-gray-800"}
                  textColor={isActive ? config.textColor : "text-gray-400 dark:text-gray-500"}
                  borderColor={isActive ? config.borderColor : "border-gray-200 dark:border-gray-700"}
                  isActive={isActive}
                />
              );
            })}
            
            {/* Final Summary and Total Carbon Footprint */}
            {(finalSummary || totalCarbonFootprint !== null) && (
              <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/30 border border-green-200 rounded-lg">
                <h3 className="text-xl font-bold text-green-800 dark:text-green-200 flex items-center gap-2 mb-3">
                  <span>🌍</span>
                  <span>Overall Analysis</span>
                </h3>
                
                {totalCarbonFootprint !== null && (
                  <div className="text-2xl font-bold text-green-700 dark:text-green-300 mb-3">
                    Total Carbon Footprint: {totalCarbonFootprint.toFixed(2)} kg CO₂e
                  </div>
                )}
                
                {finalSummary && (
                  <div className="text-green-800 dark:text-green-200">
                    {finalSummary}
                  </div>
                )}
              </div>
            )}
            
            {/* Completion message */}
            {!isConnected && Object.values(agents).some(agent => agent.isCompleted) && (
              <div className="text-gray-500 italic mt-4 text-center py-2 border-t border-gray-200">
                <span role="img" aria-label="complete" className="mr-2">🎉</span>
                Analysis complete!
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
