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
  textColor = 'text-gray-800',
  isActive = true // New prop to control "grayed out" state
}: AgentSectionProps & { isActive?: boolean }) { // Add isActive to props
  const [isOpen, setIsOpen] = useState(false);

  // Determine opacity based on isActive
  const sectionOpacity = isActive ? 'opacity-100' : 'opacity-60';

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
    <div className={`mb-4 border rounded-lg ${borderColor} ${sectionOpacity} overflow-hidden transition-opacity duration-300`}>
      <div 
        className={`flex items-center justify-between p-4 cursor-pointer ${bgColor} ${textColor}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">{iconElement}</span>
          <div>
            <h3 className={`font-medium text-lg capitalize ${!isActive && 'italic'}`}>{title || agentKey} Analysis {!isActive && <span className="text-xs">(Pending)</span>}</h3>
            {isActive && summary && !isOpen && (
              <p className={`text-sm ${isActive ? 'text-gray-600 dark:text-gray-400' : 'text-gray-400 dark:text-gray-500'} mt-1 line-clamp-1`}>{summary}</p>
            )}
            {isActive && carbon !== undefined && !isNaN(carbon) && (
              <div className={`text-sm font-medium mt-1 ${!isActive && 'text-gray-400 dark:text-gray-500'}`}>
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
        <div className={`p-4 border-t ${isActive ? borderColor : 'border-gray-200 dark:border-gray-700'} text-sm max-h-[400px] overflow-y-auto`}>
          {isActive && summary && (
            <div className={`p-3 mb-4 rounded-md ${bgColor} ${textColor} font-medium`}>
              <div className="flex items-center gap-2 mb-1">
                <span>{iconElement}</span>
                <span className="capitalize font-bold">{title || agentKey} Summary</span>
              </div>
              <div>{summary}</div>
            </div>
          )}
          {isActive && content && (
             <div className="space-y-1">
              {content}
            </div>
          )}
          {!isActive && (
            <div className="text-center py-4 text-gray-400 dark:text-gray-500 italic">
              Waiting for data for {title || agentKey}...
            </div>
          )}
        </div>
      )}
    </div>
  );
}
