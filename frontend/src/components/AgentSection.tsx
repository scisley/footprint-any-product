'use client';

import { useState } from 'react';
import { AgentSectionProps } from '@/types/components';

export function AgentSection({ 
  title, 
  icon, 
  agentKey, 
  summary, 
  content,
  isCompleted = false,
  carbon,
  borderColor = 'border-gray-200',
  bgColor = 'bg-gray-50',
  textColor = 'text-gray-800'
}: AgentSectionProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Handle the icon based on agent type
  let iconElement = icon;
  if (!icon) {
    switch (agentKey) {
      case "materials": iconElement = "🧪"; break;
      case "manufacturing": iconElement = "🏭"; break;
      case "packaging": iconElement = "📦"; break;
      case "transportation": iconElement = "🚢"; break;
      case "use": iconElement = "🔌"; break;
      case "eol": iconElement = "♻️"; break;
      default: iconElement = "🔍"; break;
    }
  }

  return (
    <div className={`mb-4 border rounded-lg ${borderColor} overflow-hidden`}>
      <div 
        className={`flex items-center justify-between p-4 cursor-pointer ${bgColor} ${textColor}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">{iconElement}</span>
          <div>
            <h3 className="font-medium text-lg capitalize">{title || agentKey} Analysis</h3>
            {summary && !isOpen && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-1">{summary}</p>
            )}
            {carbon !== undefined && !isNaN(carbon) && (
              <div className="text-sm font-medium mt-1">
                Carbon Impact: {carbon.toFixed(2)} kg CO₂e
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isCompleted && (
            <span className="text-green-500 dark:text-green-400">✓</span>
          )}
          <span className="text-xl">
            {isOpen ? '▼' : '▶'}
          </span>
        </div>
      </div>
      
      {isOpen && (
        <div className="p-4 border-t border-gray-200 text-sm max-h-[400px] overflow-y-auto">
          {summary && (
            <div className={`p-3 mb-4 rounded-md ${bgColor} ${textColor} font-medium`}>
              <div className="flex items-center gap-2 mb-1">
                <span>{iconElement}</span>
                <span className="capitalize font-bold">{title || agentKey} Summary</span>
              </div>
              <div>{summary}</div>
            </div>
          )}
          <div className="space-y-1">
            {content}
          </div>
        </div>
      )}
    </div>
  );
}