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
  
  // State for page analysis results
  const [pageAnalysis, setPageAnalysis] = useState<PageAnalysisData>({});

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
          setPageAnalysis({}); // Reset page analysis state
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
          
          // --- Handle Page Analysis Messages ---
          if (message.startsWith('PageAnalysisBrand:')) {
            setPageAnalysis(prev => ({ ...prev, brand: message.substring(18).trim() }));
          } else if (message.startsWith('PageAnalysisCategory:')) {
            setPageAnalysis(prev => ({ ...prev, category: message.substring(21).trim() }));
          } else if (message.startsWith('PageAnalysisShortDescription:')) {
            setPageAnalysis(prev => ({ ...prev, shortDescription: message.substring(29).trim() }));
          } else if (message.startsWith('PageAnalysisLongDescription:')) {
            setPageAnalysis(prev => ({ ...prev, longDescription: message.substring(28).trim() }));
          } else if (message.startsWith('PageAnalysisImageUrls:')) {
             try {
                const urls = JSON.parse(message.substring(22).trim());
                if (Array.isArray(urls)) {
                    setPageAnalysis(prev => ({ ...prev, productImageUrls: urls }));
                }
             } catch (e) {
                console.error("Failed to parse PageAnalysisImageUrls:", e);
             }
          }
          // --- Handle Agent Messages ---
          else if (message.startsWith('Agent(')) {
            // Process agent thinking
            try {
              const agentMatch = message.match(/^Agent\(([^)]+)\):/);
              if (agentMatch) {
                const agentName = agentMatch[1];
                const content = message.substring(message.indexOf(':') + 1).trim();
                
                setAgents(prev => {
                  const agentData = prev[agentName] || { messages: [], summary: '', carbon: null, isCompleted: false };
                  
                  // Prevent duplicate "thinking" messages for the planner
                  if (agentName === 'planner') {
                    const isDuplicate = agentData.messages.some(
                      (existingMsg) => existingMsg.type === 'thinking' && existingMsg.content === content
                    );
                    if (isDuplicate) {
                      return prev; // Don't add the duplicate message
                    }
                  }
                  
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
              const agentMatch = message.match(/^AgentTool\(([^)]+)\):/);
              if (agentMatch) {
                const agentName = agentMatch[1];
                const toolData = message.substring(message.indexOf(':') + 1).trim();

                try {
                  // Parse the JSON data for the tool call
                  const toolInfo = JSON.parse(toolData);
                  const toolName = toolInfo.name;
                  const toolArgs = toolInfo.args;
                  const toolId = toolInfo.id;

                  // Format args for display
                  let formattedArgs = '';
                  if (toolArgs) {
                    if (typeof toolArgs === 'object') {
                      formattedArgs = Object.entries(toolArgs)
                        .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
                        .join(', ');
                    } else {
                      formattedArgs = String(toolArgs);
                    }
                  }

                  const toolContent = `${toolName}(${formattedArgs})`; // Construct the content for checking and storing

                  setAgents(prev => {
                    const agentData = prev[agentName] || { messages: [], summary: '', carbon: null, isCompleted: false };

                    // Prevent duplicate "tool" messages
                    const isDuplicateToolCall = agentData.messages.some(
                      (existingMsg) => existingMsg.type === 'tool' && existingMsg.content === toolContent
                    );
                    if (isDuplicateToolCall) {
                      return prev; // Don't add the duplicate message
                    }

                    return {
                      ...prev,
                      [agentName]: {
                        ...agentData,
                        messages: [...agentData.messages, {
                          type: 'tool',
                          content: toolContent,
                          toolId: toolId,
                          toolName: toolName,
                          toolArgs: toolArgs
                        }],
                      }
                    };
                  });
                } catch (parseErr) {
                  console.error('[Tool JSON Parse Error]:', parseErr);
                  // Fallback to legacy format if JSON parsing fails
                  const legacyMatch = message.match(/^AgentTool\(([^)]+)\):\s*(\w+)\((.*)\)/);
                  if (legacyMatch) {
                    const agentName = legacyMatch[1];
                    const toolName = legacyMatch[2];
                    const toolArgs = legacyMatch[3];
                    const toolContent = `${toolName}(${toolArgs})`;

                    setAgents(prev => {
                      const agentData = prev[agentName] || { messages: [], summary: '', carbon: null, isCompleted: false };
                      return {
                        ...prev,
                        [agentName]: {
                          ...agentData,
                          messages: [...agentData.messages, { type: 'tool', content: toolContent }],
                        }
                      };
                    });
                  }
                }
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
                const obsData = message.substring(message.indexOf(':') + 1).trim();

                try {
                  // Try to parse the JSON data
                  const obsInfo = JSON.parse(obsData);
                  const observation = obsInfo.content;
                  const toolCallId = obsInfo.tool_call_id || '';
                  const toolName = obsInfo.tool_name || '';

                  setAgents(prev => {
                    const agentData = prev[agentName] || { messages: [], summary: '', carbon: null, isCompleted: false };
                    return {
                      ...prev,
                      [agentName]: {
                        ...agentData,
                        messages: [...agentData.messages, {
                          type: 'observation',
                          content: observation,
                          toolCallId: toolCallId,
                          toolName: toolName
                        }],
                      }
                    };
                  });
                } catch (jsonErr) {
                  console.error('[Observation JSON Parse Error]:', jsonErr);
                  // Fallback to legacy format
                  const observation = obsData;
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
        // Check if we have enhanced tool information
        const hasEnhancedInfo = 'toolName' in msg && 'toolArgs' in msg;

        if (hasEnhancedInfo) {
          // Access the enhanced tool information
          const toolName = msg.toolName as string;
          const toolArgs = msg.toolArgs as Record<string, any>;
          const toolId = (msg as any).toolId || '';

          return (
            <div key={index} className="pl-4 my-1 border-l-2 border-blue-200 text-gray-600 dark:text-gray-400 text-xs">
              <div className="font-mono mb-1">
                <span className="text-blue-600 dark:text-blue-400 font-medium">Using tool: </span>
                <span className="text-emerald-600 dark:text-emerald-400">{toolName}</span>
                {toolId && <span className="opacity-50 text-xs ml-1">#{toolId.substring(0, 6)}</span>}
              </div>

              {toolArgs && typeof toolArgs === 'object' && Object.keys(toolArgs).length > 0 && (
                <div className="bg-gray-50 dark:bg-gray-800 p-2 rounded font-mono text-xxs overflow-x-auto">
                  {Object.entries(toolArgs).map(([key, value], i) => (
                    <div key={i} className="flex">
                      <span className="text-blue-500 dark:text-blue-400 mr-2">{key}:</span>
                      <span className="text-gray-700 dark:text-gray-300 break-all">
                        {typeof value === 'object'
                          ? JSON.stringify(value)
                          : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        }

        // Fallback to original display if we don't have enhanced data
        return (
          <div key={index} className="pl-4 my-1 border-l-2 border-blue-200 text-gray-600 dark:text-gray-400 text-xs font-mono">
            <span className="text-blue-600 dark:text-blue-400">Using tool:</span>
            <span className="opacity-75"> {msg.content}</span>
          </div>
        );
      } else if (msg.type === 'observation') {
        // Check if we have enhanced observation information
        const hasEnhancedInfo = 'toolCallId' in msg || 'toolName' in msg;
        const toolCallId = (msg as any).toolCallId;
        const toolName = (msg as any).toolName;

        return (
          <div key={index} className={`pl-4 my-1 border-l-2 ${hasEnhancedInfo ? 'border-teal-200' : 'border-gray-200'} text-gray-500 dark:text-gray-400 text-xs`}>
            <div className="flex items-center mb-0.5">
              <span className={`${hasEnhancedInfo ? 'text-teal-600 dark:text-teal-400' : 'opacity-75'} font-medium`}>
                Result{toolName ? ` from ${toolName}` : ''}:
              </span>
              {toolCallId && (
                <span className="opacity-50 text-xxs ml-1">#{toolCallId.substring(0, 6)}</span>
              )}
            </div>
            <div className="mt-1 bg-gray-50 dark:bg-gray-800 p-1.5 rounded">
              {msg.content}
            </div>
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
  if (!isStreaming && !isConnecting && !Object.values(agents).some(agent => agent.messages.length > 0) && Object.keys(pageAnalysis).length === 0) {
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
        ) : isConnecting && !isConnected && Object.keys(pageAnalysis).length === 0 && !Object.values(agents).some(agent => agent.messages.length > 0) ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin h-8 w-8 border-4 border-gray-200 border-t-[var(--primary)] rounded-full mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Establishing connection and preparing analysis...</p>
            <p className="text-xs text-gray-500 mt-2">This may take a few seconds</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Page Analysis Section */}
            {(pageAnalysis.brand || pageAnalysis.category || pageAnalysis.shortDescription || pageAnalysis.longDescription || (pageAnalysis.productImageUrls && pageAnalysis.productImageUrls.length > 0)) && (
                <div className="mb-4 border rounded-lg border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 overflow-hidden">
                    <div className="flex items-center justify-between p-4 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                        <div className="flex items-center gap-3">
                            <span className="text-xl">📄</span>
                            <h3 className="font-medium text-lg">Page Analysis Results</h3>
                        </div>
                    </div>
                    <div className="p-4 text-sm text-gray-700 dark:text-gray-300">
                        {pageAnalysis.brand && <p><strong>Brand:</strong> {pageAnalysis.brand}</p>}
                        {pageAnalysis.category && <p><strong>Category:</strong> {pageAnalysis.category}</p>}
                        {pageAnalysis.shortDescription && <p><strong>Short Description:</strong> {pageAnalysis.shortDescription}</p>}
                        {pageAnalysis.longDescription && (
                            <div className="mt-3">
                                <strong>Long Description:</strong>
                                <div className="mt-1 p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md max-h-40 overflow-y-auto">
                                    {pageAnalysis.longDescription}
                                </div>
                            </div>
                        )}
                        {pageAnalysis.productImageUrls && pageAnalysis.productImageUrls.length > 0 && (
                            <div className="mt-3">
                                <strong>Images Found:</strong>
                                <div className="flex flex-wrap gap-2 mt-1 max-h-24 overflow-y-auto">
                                    {pageAnalysis.productImageUrls.map((imgUrl, idx) => (
                                        <img 
                                            key={idx} 
                                            src={imgUrl} 
                                            alt={`Product image ${idx + 1}`} 
                                            className="h-16 w-16 object-cover rounded-md border border-gray-200 dark:border-gray-700"
                                        />
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

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
