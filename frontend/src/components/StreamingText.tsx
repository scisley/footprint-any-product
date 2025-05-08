'use client';

import { useEffect, useRef, useState } from 'react';
import { StreamingTextProps } from '@/types/components';

export function StreamingText({
  url = 'ws://localhost:3005/ws',
  isStreaming,
  brand,
  category,
  description,
  onStreamingComplete
}: StreamingTextProps) {
  const [text, setText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const hasInitializedRef = useRef(false);

  useEffect(() => {
    console.log('[StreamingText useEffect] Triggered. Props:', { isStreaming, brand, category, description, wsRef: wsRef.current });

    // Logic to establish or close WebSocket connection based on props
    if (isStreaming && brand && category && description) {
      // Only attempt to connect if not already connected
      if (!wsRef.current) {
        console.log('[StreamingText useEffect] Conditions met. Attempting to establish WebSocket connection to:', url);
        try {
          const socket = new WebSocket(url);
          wsRef.current = socket; // Assign the socket to the ref immediately

          socket.onopen = () => {
            console.log('[StreamingText WebSocket] Connection opened.');
            setIsConnected(true);
            setError(null);
            setText(''); // Clear previous text
            hasInitializedRef.current = true; // Mark that we've initialized a connection attempt
            
            const payload = JSON.stringify({ brand, category, description });
            console.log('[StreamingText WebSocket] Sending payload:', payload);
            socket.send(payload);
          };

          socket.onmessage = (event) => {
            const message = event.data;
            console.log('[StreamingText WebSocket] Message received:', message);
            
            // Existing detailed message logging can remain here...
            if (message.startsWith('Agent(')) {
              try {
                const agentMatch = message.match(/^Agent\(([^)]+)\):/);
                const agentName = agentMatch ? agentMatch[1] : "unknown";
                const content = message.substring(message.indexOf(':') + 1).trim();
                console.log('[Agent Message]:', {agent: agentName, content: content.substring(0, 50) + '...'});
              } catch (err) {
                console.error('[Agent Message Parse Error]:', err);
              }
            } else if (message.startsWith('AgentAction(')) {
              try {
                const agentMatch = message.match(/^AgentAction\(([^)]+)\):/);
                const agentName = agentMatch ? agentMatch[1] : "unknown";
                console.log('[Agent Action]:', {agent: agentName});
              } catch (err) {
                console.error('[Agent Action Parse Error]:', err);
              }
            } else if (message.startsWith('AgentTool(')) {
              try {
                const agentMatch = message.match(/^AgentTool\(([^)]+)\):/);
                const agentName = agentMatch ? agentMatch[1] : "unknown";
                console.log('[Agent Tool Use]:', {agent: agentName});
              } catch (err) {
                console.error('[Agent Tool Parse Error]:', err);
              }
            } else if (message.startsWith('SystemMessage:')) {
              console.log('[System Message]:', message.substring(14));
            } else if (message.startsWith('PhaseStart:')) {
              console.log('[Phase Start]:', message.substring(11));
            } else if (message.startsWith('PhaseSummary(')) {
              try {
                const phaseMatch = message.match(/^PhaseSummary\(([^)]+)\):/);
                const phaseName = phaseMatch ? phaseMatch[1] : "unknown";
                console.log('[Phase Summary]:', {phase: phaseName});
              } catch (err) {
                console.error('[Phase Summary Parse Error]:', err);
              }
            } else if (message.startsWith('FinalSummary:')) {
              console.log('[Final Summary]:', message.substring(13).substring(0, 50) + '...');
            } else if (message.startsWith('CarbonFootprint:')) {
              console.log('[Carbon Footprint]:', message.substring(16));
            } else if (message.startsWith('AgentStatus(')) {
              try {
                const statusMatch = message.match(/^AgentStatus\(([^)]+)\):/);
                const agentName = statusMatch ? statusMatch[1] : "unknown";
                console.log('[Agent Status]:', {agent: agentName});
              } catch (err) {
                console.error('[Agent Status Parse Error]:', err);
              }
            }

            setText((prev) => prev + message + "\n");
            
            if (contentRef.current) {
              contentRef.current.scrollTop = contentRef.current.scrollHeight;
            }
            
            if (message === "AnalysisComplete") {
              console.log('[StreamingText WebSocket] AnalysisComplete message received.');
              onStreamingComplete?.();
            }
          };

          socket.onclose = (event) => {
            console.log('[StreamingText WebSocket] Connection closed.', event.reason, event.code);
            setIsConnected(false);
            // Only call onStreamingComplete if the connection was intentionally closed after starting.
            // Avoid calling it if the connection failed to open.
            if (hasInitializedRef.current && !error) { 
              onStreamingComplete?.();
            }
          };

          socket.onerror = (errEvent) => {
            // Type assertion for errEvent if needed, or use a generic error.
            const errorMessage = 'WebSocket error occurred. Check console for details.';
            console.error('[StreamingText WebSocket] Error:', errEvent);
            setError(errorMessage);
            setIsConnected(false);
            // Potentially call onStreamingComplete here if an error means the stream is over.
            // onStreamingComplete?.(); 
          };
        } catch (err) {
          console.error('[StreamingText useEffect] Error establishing WebSocket connection:', err);
          setError('Failed to initialize WebSocket connection.');
          setIsConnected(false);
        }
      }
    } else {
      // Conditions for streaming not met (e.g., isStreaming is false)
      // If there's an existing connection, close it.
      if (wsRef.current) {
        console.log('[StreamingText useEffect] isStreaming is false or product details missing. Closing existing WebSocket.');
        wsRef.current.close();
        wsRef.current = null; // Clear the ref
        setIsConnected(false);
      }
    }

    // Cleanup function: will run when component unmounts or dependencies change
    return () => {
      if (wsRef.current) {
        console.log('[StreamingText useEffect Cleanup] Closing WebSocket connection due to unmount or prop change.');
        wsRef.current.close();
        wsRef.current = null;
        setIsConnected(false);
      }
    };
  }, [isStreaming, url, brand, category, description, onStreamingComplete]);

  // Format the text with markdown-like syntax
  const formatText = (text: string) => {
    const lines = text.split('\n');
    console.log('[Formatting Text]:', lines.length, 'lines');
    
    // Group similar consecutive lines for better debugging
    const agentLines = lines.filter(line => line.startsWith('Agent(')).length;
    const systemLines = lines.filter(line => line.startsWith('System:')).length;
    const phaseLines = lines.filter(line => line.startsWith('Phase:')).length;
    console.log('[Line Stats]:', {
      agent: agentLines, 
      system: systemLines,
      phase: phaseLines,
      total: lines.length
    });
    
    return lines.map((line, index) => {
      // Skip empty lines
      if (!line.trim()) {
        return null;
      }
      
      // Shorter log prefix to reduce console noise
      const shortLine = line.substring(0, 30) + (line.length > 30 ? '...' : '');
      if (index < 20 || index % 10 === 0) { // Only log some lines to avoid flooding
        console.log(`[L${index}]:`, shortLine);
      }
      
      if (line.startsWith('PhaseStart:')) {
        // Extract the phase name
        const phaseName = line.substring(11).trim();
        return (
          <div key={index} className="font-bold text-[var(--primary)] mt-6 mb-2 text-lg border-b border-gray-200 pb-1">
            <span role="img" aria-label="phase" className="mr-2">🔍</span>
            Phase: {phaseName}
          </div>
        );
      } else if (line.startsWith('FinalSummary:')) {
        const summary = line.substring(13).trim();
        return (
          <div key={index} className="font-bold text-green-600 mt-6 border-t border-green-200 pt-3 text-lg">
            <span role="img" aria-label="summary" className="mr-2">✅</span>
            {summary}
          </div>
        );
      } else if (line.startsWith('CarbonFootprint:')) {
        const carbonValue = line.substring(16).trim();
        return (
          <div key={index} className="font-bold text-green-800 my-2 text-xl">
            <span role="img" aria-label="carbon" className="mr-2">🌍</span>
            {carbonValue} kg CO2e
          </div>
        );
      } else if (line.startsWith('PhaseSummary(')) {
        // Extract phase name and summary
        const phaseMatch = line.match(/^PhaseSummary\(([^)]+)\):\s*(.*)/);
        if (!phaseMatch) return <div key={index}>{line}</div>;
        
        const phaseName = phaseMatch[1];
        const summary = phaseMatch[2];
        
        let phaseIcon = "📊";
        let bgColorClass = "bg-blue-50 dark:bg-blue-900/30";
        let textColorClass = "text-blue-800 dark:text-blue-200";
        
        switch (phaseName) {
          case "manufacturing":
            phaseIcon = "🏭";
            bgColorClass = "bg-blue-50 dark:bg-blue-900/30";
            textColorClass = "text-blue-800 dark:text-blue-200";
            break;
          case "packaging":
            phaseIcon = "📦";
            bgColorClass = "bg-amber-50 dark:bg-amber-900/30";
            textColorClass = "text-amber-800 dark:text-amber-200";
            break;
          case "transportation":
            phaseIcon = "🚢";
            bgColorClass = "bg-indigo-50 dark:bg-indigo-900/30";
            textColorClass = "text-indigo-800 dark:text-indigo-200";
            break;
          case "use":
            phaseIcon = "🔌";
            bgColorClass = "bg-green-50 dark:bg-green-900/30";
            textColorClass = "text-green-800 dark:text-green-200";
            break;
          case "eol":
            phaseIcon = "♻️";
            bgColorClass = "bg-purple-50 dark:bg-purple-900/30";
            textColorClass = "text-purple-800 dark:text-purple-200";
            break;
        }
        
        return (
          <div key={index} className={`p-3 my-2 rounded-md ${bgColorClass} ${textColorClass} font-medium`}>
            <div className="flex items-center gap-2 mb-1">
              <span>{phaseIcon}</span>
              <span className="capitalize font-bold">{phaseName} Summary</span>
            </div>
            <div>{summary}</div>
          </div>
        );
      } else if (line.startsWith('Agent(')) {
        // Extract agent name from the format Agent(name): message
        console.log('[Agent Raw]:', line);
        const agentMatch = line.match(/^Agent\(([^)]+)\):/);
        
        if (!agentMatch) {
          console.log('[Agent Parse Error]: Could not extract agent name', line);
          // Fallback for poorly formatted agent messages
          return <div key={index}>{line}</div>;
        }
        
        const agentName = agentMatch[1];
        const message = line.substring(line.indexOf(':') + 1).trim();
        
        console.log('[Agent Parsed]:', agentName, '-', message.substring(0, 30) + (message.length > 30 ? '...' : ''));
        
        // Use different styling for different agent types
        let agentIcon = "💬";
        let borderColorClass = "border-blue-300";
        let textColorClass = "text-blue-600 dark:text-blue-400";
        
        switch (agentName) {
          case "manufacturing":
            agentIcon = "🏭";
            borderColorClass = "border-blue-300";
            textColorClass = "text-blue-600 dark:text-blue-400";
            break;
          case "packaging":
            agentIcon = "📦";
            borderColorClass = "border-amber-300";
            textColorClass = "text-amber-600 dark:text-amber-400";
            break;
          case "transportation":
            agentIcon = "🚢";
            borderColorClass = "border-indigo-300";
            textColorClass = "text-indigo-600 dark:text-indigo-400";
            break;
          case "use":
            agentIcon = "🔌";
            borderColorClass = "border-green-300";
            textColorClass = "text-green-600 dark:text-green-400";
            break;
          case "eol":
            agentIcon = "♻️";
            borderColorClass = "border-purple-300";
            textColorClass = "text-purple-600 dark:text-purple-400";
            break;
        }
        
        return (
          <div key={index} className={`pl-4 my-1.5 border-l-2 ${borderColorClass} text-gray-800 dark:text-gray-300 py-1`}>
            <span className={`text-xs ${textColorClass} font-medium mr-2`}>
              <span className="mr-1">{agentIcon}</span>
              {agentName}:
            </span>
            {message}
          </div>
        );
      } else if (line.startsWith('AgentAction(')) {
        // Extract agent name and action
        const agentMatch = line.match(/^AgentAction\(([^)]+)\):/);
        if (!agentMatch) return <div key={index}>{line}</div>;
        
        const agentName = agentMatch[1];
        const action = line.substring(line.indexOf(':') + 1).trim();
        
        // Agent icons by type
        let agentIcon = "🔄";
        switch (agentName) {
          case "manufacturing": agentIcon = "🏭"; break;
          case "packaging": agentIcon = "📦"; break;
          case "transportation": agentIcon = "🚢"; break;
          case "use": agentIcon = "🔌"; break;
          case "eol": agentIcon = "♻️"; break;
        }
        
        return (
          <div key={index} className="pl-4 my-1 border-l-2 border-gray-300 text-gray-600 dark:text-gray-400 text-sm italic">
            <span className="text-xs font-medium mr-2">
              <span className="mr-1">{agentIcon}</span>
              {agentName} action:
            </span>
            {action}
          </div>
        );
      } else if (line.startsWith('AgentTool(')) {
        // Extract agent name and tool details
        const agentMatch = line.match(/^AgentTool\(([^)]+)\):\s*(\w+)\((.*)\)/);
        if (!agentMatch) return <div key={index}>{line}</div>;
        
        const agentName = agentMatch[1];
        const toolName = agentMatch[2];
        const toolArgs = agentMatch[3];
        
        return (
          <div key={index} className="pl-4 my-1 border-l-2 border-blue-200 text-gray-600 dark:text-gray-400 text-xs font-mono">
            <span className="text-blue-600 dark:text-blue-400">
              {agentName} using {toolName}
            </span>
            <span className="opacity-75"> with args: {toolArgs}</span>
          </div>
        );
      } else if (line.startsWith('AgentObs(')) {
        // Extract agent name and observation
        const agentMatch = line.match(/^AgentObs\(([^)]+)\):/);
        if (!agentMatch) return <div key={index}>{line}</div>;
        
        const agentName = agentMatch[1];
        const observation = line.substring(line.indexOf(':') + 1).trim();
        
        return (
          <div key={index} className="pl-4 my-1 border-l-2 border-gray-200 text-gray-500 dark:text-gray-400 text-xs">
            <span className="opacity-75">Observation for {agentName}:</span> {observation}
          </div>
        );
      } else if (line.startsWith('SystemMessage:')) {
        console.log('[System Raw]:', line);
        const message = line.substring(14).trim();
        console.log('[System Parsed]:', message.substring(0, 30) + (message.length > 30 ? '...' : ''));
        return (
          <div key={index} className="pl-4 my-1 border-l-2 border-purple-300 text-gray-800 dark:text-gray-300">
            <span className="text-xs text-purple-600 dark:text-purple-400 font-medium mr-2">System:</span>
            {message}
          </div>
        );
      } else if (line.startsWith('AgentStatus(')) {
        // Extract agent name and status
        const statusMatch = line.match(/^AgentStatus\(([^)]+)\):\s*(.*)/);
        if (!statusMatch) return <div key={index}>{line}</div>;
        
        const agentName = statusMatch[1];
        const status = statusMatch[2];
        
        // Icon based on agent type
        let agentIcon = "📊";
        switch (agentName) {
          case "manufacturing": agentIcon = "🏭"; break;
          case "packaging": agentIcon = "📦"; break;
          case "transportation": agentIcon = "🚢"; break;
          case "use": agentIcon = "🔌"; break;
          case "eol": agentIcon = "♻️"; break;
        }
        
        return (
          <div key={index} className="flex items-center gap-2 my-2 p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
            <div className="text-lg">{agentIcon}</div>
            <div>
              <div className="text-sm font-medium capitalize">{agentName} Agent</div>
              <div className="text-xs text-gray-600 dark:text-gray-400">{status}</div>
            </div>
          </div>
        );
      } else if (line === "AnalysisComplete") {
        return (
          <div key={index} className="text-gray-500 italic mt-4 text-center py-2 border-t border-gray-200">
            <span role="img" aria-label="complete" className="mr-2">🎉</span>
            Analysis complete!
          </div>
        );
      } else if (line.trim() === '') {
        return <br key={index} />;
      } else {
        return <div key={index}>{line}</div>;
      }
    });
  };

  if (!isStreaming && !text) {
    return null;
  }

  return (
    <div className="w-full max-w-3xl mx-auto mt-8">
      <div className="rounded-lg border border-[var(--border)] bg-white dark:bg-gray-900 p-4 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-medium">Carbon Footprint Analysis</h3>
          {isConnected && (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Generating analysis...</span>
            </div>
          )}
        </div>
        
        <div 
          ref={contentRef}
          className="streaming-text min-h-[200px] max-h-[500px] overflow-y-auto mt-4 font-mono text-sm p-2"
        >
          {error ? (
            <div className="text-red-500">{error}</div>
          ) : (
            text ? (
              <>
                {formatText(text)}
              </>
            ) : (
              <div className="text-gray-400 dark:text-gray-600 italic">
                Analysis will appear here...
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
