import React from 'react';
import Link from 'next/link';
import { ResultsTableProps } from '../../types';

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

// Get color based on carbon score
const getScoreColor = (score: number) => {
  if (score < 40) return 'var(--score-good)';
  if (score < 60) return 'var(--score-fair)';
  return 'var(--score-poor)';
};

const ResultsTable: React.FC<ResultsTableProps> = ({ results, isLoading, error }) => {
  if (isLoading) {
    return (
      <div className="py-8 text-center">
        <div className="inline-block animate-spin mr-2">
          <svg className="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        <span>Loading results...</span>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="py-8 text-center" style={{ color: 'var(--status-error)' }}>
        {error}
      </div>
    );
  }
  
  if (results.length === 0) {
    return (
      <div className="py-8 text-center">
        No analysis results found.
      </div>
    );
  }
  
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b" style={{ borderColor: 'var(--card-border)' }}>
            <th className="py-3 px-4 text-left">Product</th>
            <th className="py-3 px-4 text-left">Date Analyzed</th>
            <th className="py-3 px-4 text-center">Carbon Score</th>
            <th className="py-3 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {results.map((result) => (
            <tr 
              key={result.id} 
              className="border-b hover:bg-opacity-50" 
              style={{ 
                borderColor: 'var(--card-border)',
                transition: 'all 0.2s'
              }}
            >
              <td className="py-4 px-4">
                <div className="font-medium" style={{ color: 'var(--foreground)' }}>
                  {result.product_name || 'Unnamed Product'}
                </div>
                <div className="text-xs mt-1 truncate max-w-64" style={{ color: 'var(--score-neutral)' }}>
                  {result.product_url}
                </div>
              </td>
              <td className="py-4 px-4" style={{ color: 'var(--foreground)' }}>
                {formatDate(result.timestamp)}
              </td>
              <td className="py-4 px-4 text-center">
                <div 
                  className="inline-flex items-center justify-center font-bold rounded-full w-12 h-12"
                  style={{ 
                    backgroundColor: getScoreColor(result.overall_score),
                    color: 'white'
                  }}
                >
                  {result.overall_score}
                </div>
              </td>
              <td className="py-4 px-4 text-right">
                <Link
                  href={`/result/${result.id}`}
                  className="eco-button text-sm px-3 py-1.5 rounded inline-flex items-center"
                  style={{ 
                    backgroundColor: 'var(--button-hover)',
                    border: '1px solid var(--card-border)',
                    color: 'var(--foreground)'
                  }}
                >
                  View Details
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ResultsTable;