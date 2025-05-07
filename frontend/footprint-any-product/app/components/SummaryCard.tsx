import React from 'react';
import CarbonScore from './CarbonScore';
import StatusIndicator from './StatusIndicator';
import { SummaryIcon, ExpandIcon, CodeIcon, ChartIcon, LeafIcon } from './Icons';

// Import types from central location
import { SummaryCardProps } from '../types';

const SummaryCard: React.FC<SummaryCardProps> = ({
  agent,
  isExpanded,
  showRawJson,
  onToggleDetails,
  onToggleRawJson
}) => {
  // Check if the agent has completed its analysis
  const isCompleted = agent.status.startsWith('Completed');
  
  return (
    <div 
      className="rounded-lg w-full overflow-hidden"
      style={{ 
        backgroundColor: 'var(--card-background)',
        borderWidth: '1px',
        borderColor: 'var(--card-border)',
        borderTopWidth: '4px',
        borderTopColor: 'var(--primary)',
        boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1)'
      }}
    >
      {/* Card Header */}
      <div className="p-5">
        <div className="flex justify-between items-center mb-4 pb-2" style={{ borderBottom: '1px solid var(--card-border)' }}>
          <div className="flex items-center">
            <div className="mr-3 text-primary"><SummaryIcon /></div>
            <h2 
              className="font-bold text-xl"
              style={{ color: 'var(--foreground)' }}
            >
              Overall Analysis Summary
            </h2>
          </div>
          
          {isCompleted && (
            <div className="flex gap-2">
              <button 
                className="eco-button text-xs px-2 py-1 rounded flex items-center"
                style={{ 
                  color: 'var(--foreground)',
                  border: '1px solid var(--card-border)',
                  backgroundColor: isExpanded && !showRawJson ? 'var(--button-hover)' : 'transparent'
                }}
                onClick={onToggleDetails}
              >
                <span className="mr-1"><ExpandIcon /></span>
                {isExpanded && !showRawJson ? 'Hide Details' : 'Details'}
              </button>
              
              <button 
                className="eco-button text-xs px-2 py-1 rounded flex items-center"
                style={{ 
                  color: 'var(--foreground)',
                  border: '1px solid var(--card-border)',
                  backgroundColor: showRawJson ? 'var(--button-hover)' : 'transparent'
                }}
                onClick={onToggleRawJson}
              >
                <span className="mr-1"><CodeIcon /></span>
                {showRawJson ? 'Hide JSON' : 'JSON'}
              </button>
            </div>
          )}
        </div>
        
        <div className="flex flex-col gap-4">
          {/* Status Indicator */}
          <StatusIndicator status={agent.status} />
          
          {isCompleted && (
            <>
              {/* Carbon Score Gauge */}
              <div>
                <div className="flex justify-between mb-1">
                  <div className="font-semibold" style={{ color: 'var(--foreground)' }}>
                    Overall Carbon Score:
                  </div>
                  <div className="px-3 py-1 rounded-full text-white text-sm font-medium"
                    style={{ backgroundColor: getScoreColor(agent.carbonScore) }}>
                    {agent.carbonScore}/100
                  </div>
                </div>
                <CarbonScore score={agent.carbonScore} size="lg" />
              </div>
              
              {/* Classification */}
              {agent.data?.totalCarbonFootprint && (
                <div className="p-3 rounded-lg mt-2" style={{ 
                  backgroundColor: `${getScoreColor(agent.carbonScore)}15`,
                  border: `1px solid ${getScoreColor(agent.carbonScore)}30`
                }}>
                  <div className="font-semibold mb-1">Classification:</div>
                  <div className="text-lg">
                    {agent.data.totalCarbonFootprint.classification}
                  </div>
                  <div className="text-sm mt-1 opacity-80">
                    {agent.data.totalCarbonFootprint.comparativeRanking}
                  </div>
                </div>
              )}
              
              {/* Recommendation */}
              {agent.data?.consumerRecommendation && (
                <div className="mt-4">
                  <div className="font-semibold mb-2">Recommendation:</div>
                  <div className="p-4 rounded-lg" style={{ 
                    backgroundColor: 'rgba(0, 0, 0, 0.03)',
                    border: '1px solid var(--card-border)'
                  }}>
                    {agent.data.consumerRecommendation}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
      
      {/* Expanded Details */}
      {isExpanded && !showRawJson && isCompleted && agent.data && (
        <div 
          className="px-5 pb-5"
          style={{ color: 'var(--foreground)' }}
        >
          {/* Breakdown */}
          {agent.data.totalCarbonFootprint?.breakdown && (
            <div className="mb-6">
              <h3 className="font-semibold mb-3 flex items-center">
                <ChartIcon />
                <span className="ml-2">Carbon Score Breakdown</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(agent.data.totalCarbonFootprint.breakdown).map(([key, value], index) => (
                  <div 
                    key={index}
                    className="p-3 rounded-lg"
                    style={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}
                  >
                    <div className="capitalize font-medium mb-1">{key}:</div>
                    <div className="flex justify-between mb-1">
                      <span>Score:</span>
                      <span 
                        className="font-semibold"
                        style={{ color: getScoreColor(value.score) }}
                      >
                        {value.score}/100
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Contribution:</span>
                      <span>{value.contribution}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Key Impact Areas */}
            {agent.data.keyImpactAreas && (
              <div>
                <h3 className="font-semibold mb-3">Key Impact Areas</h3>
                <ul className="list-disc pl-5">
                  {agent.data.keyImpactAreas.map((item, index) => (
                    <li key={index} className="mb-1">{item}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Positive Aspects */}
            {agent.data.positiveSustainabilityAspects && (
              <div>
                <h3 className="font-semibold mb-3">Positive Sustainability Aspects</h3>
                <ul className="list-disc pl-5">
                  {agent.data.positiveSustainabilityAspects.map((item, index) => (
                    <li key={index} className="mb-1">{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          {/* Improvement Recommendations */}
          {agent.data.improvementRecommendations && (
            <div className="mb-6">
              <h3 className="font-semibold mb-3 flex items-center">
                <LeafIcon />
                <span className="ml-2">Improvement Recommendations</span>
              </h3>
              <div className="p-4 rounded-lg" style={{ 
                backgroundColor: 'var(--primary-light)',
                color: 'var(--primary-dark)'
              }}>
                <ul className="list-disc pl-5">
                  {agent.data.improvementRecommendations.map((item, index) => (
                    <li key={index} className="mb-1">{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
          
          {/* Similar Products */}
          {agent.data.similarProductsWithBetterScores && (
            <div className="mb-6">
              <h3 className="font-semibold mb-3">Similar Products with Better Scores</h3>
              <div className="flex flex-wrap gap-2">
                {agent.data.similarProductsWithBetterScores.map((product, index) => (
                  <div 
                    key={index}
                    className="pill pill-accent"
                  >
                    {product}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="mt-3 text-xs text-right opacity-60">
            {agent.timestamp && (
              <span>Last updated: {new Date(agent.timestamp).toLocaleString()}</span>
            )}
          </div>
        </div>
      )}
      
      {/* Raw JSON data */}
      {isExpanded && showRawJson && (
        <div 
          className="px-5 pb-5"
          style={{ color: 'var(--foreground)' }}
        >
          <p className="font-medium my-4">Raw Agent JSON Data:</p>
          <pre 
            className="text-xs p-3 rounded overflow-auto max-h-80"
            style={{ 
              backgroundColor: 'rgba(0, 0, 0, 0.05)',
              color: 'var(--foreground)'
            }}
          >
            {JSON.stringify(agent, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

// Helper function to get color based on score
const getScoreColor = (score: number) => {
  if (score <= 0) return 'var(--score-neutral)';
  if (score < 40) return 'var(--score-good)';
  if (score < 60) return 'var(--score-fair)';
  return 'var(--score-poor)';
};

export default SummaryCard;