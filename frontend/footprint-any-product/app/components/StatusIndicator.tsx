import React from 'react';
import { CheckIcon, LoadingIcon, InfoIcon } from './Icons';
import { StatusIndicatorProps } from '../types';

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, compact = false }) => {
  // Status color mapping
  const getStatusColor = (status: string) => {
    if (status === 'Idle') return 'var(--status-idle)';
    if (status === 'Queued') return 'var(--status-queued)';
    if (status.includes('Processing') || status === 'Processing...') return 'var(--status-processing)';
    if (status.startsWith('Completed')) return 'var(--status-completed)';
    return 'var(--status-error)'; // Default to error for unknown statuses
  };
  
  // Status icon mapping
  const getStatusIcon = (status: string) => {
    if (status.startsWith('Completed')) {
      return <CheckIcon />;
    } else if (status === 'Processing...' || status.includes('Processing')) {
      return <LoadingIcon />;
    } else {
      return <InfoIcon />;
    }
  };
  
  // Extract the display status - strip "Completed: " prefix if present
  const displayStatus = status.startsWith('Completed: ') 
    ? status.substring('Completed: '.length) 
    : status;
  
  return (
    <div 
      className={`flex items-center ${compact ? 'text-xs' : 'text-sm'}`}
      style={{ color: getStatusColor(status) }}
    >
      <span className="mr-1.5">{getStatusIcon(status)}</span>
      <span className="font-medium">{displayStatus}</span>
      
      {status === 'Processing...' && (
        <span 
          className="ml-2 inline-block h-2 w-2 rounded-full pulse"
          style={{ backgroundColor: getStatusColor(status) }} 
        ></span>
      )}
    </div>
  );
};

export default StatusIndicator;