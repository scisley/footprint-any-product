import React from 'react';
import CarbonScore from './CarbonScore';
import StatusIndicator from './StatusIndicator';
import { getAgentIcon, ExpandIcon, CodeIcon } from './Icons';

// Import types from central location
import { 
  Agent, 
  AgentData, 
  AgentCardProps,
  MaterialsData,
  ManufacturingData,
  PackagingData,
  TransportData,
  LifecycleData,
  EndOfLifeData
} from '../types';

const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  isExpanded,
  showRawJson,
  onToggleDetails,
  onToggleRawJson,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  index
}) => {
  // Check if the agent has completed its analysis
  const isCompleted = agent.status.startsWith('Completed');
  
  // Get border color based on carbon score
  const getBorderColor = () => {
    if (agent.carbonScore <= 0) return 'var(--score-neutral)';
    if (agent.carbonScore < 40) return 'var(--score-good)';
    if (agent.carbonScore < 60) return 'var(--score-fair)';
    return 'var(--score-poor)';
  };
  
  return (
    <div 
      className="eco-card rounded-lg w-full overflow-hidden"
      style={{ 
        backgroundColor: 'var(--card-background)',
        borderWidth: '1px',
        borderColor: 'var(--card-border)',
        borderLeftColor: getBorderColor(),
        borderLeftWidth: '4px',
      }}
    >
      {/* Card Header */}
      <div className="p-4">
        <div className="flex justify-between items-center mb-3">
          <div className="flex items-center">
            <div className="mr-3 text-primary">{getAgentIcon(agent.id)}</div>
            <h3 
              className="font-bold text-lg"
              style={{ color: 'var(--foreground)' }}
            >
              {agent.name}
            </h3>
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
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleDetails();
                }}
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
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleRawJson();
                }}
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
          
          {/* Carbon Score */}
          <div>
            <div className="mb-1 text-sm font-medium" style={{ color: 'var(--foreground)' }}>Carbon Score:</div>
            <CarbonScore score={agent.carbonScore} size="md" />
          </div>
        </div>
      </div>
      
      {/* Expanded Details Section */}
      {isExpanded && !showRawJson && agent.details && (
        <div 
          className="px-4 pb-4 pt-0"
          style={{ 
            borderTop: '1px solid var(--card-border)', 
            color: 'var(--foreground)'
          }}
        >
          <div className="mb-3 mt-4">
            <p><strong>Details:</strong> {agent.details}</p>
          </div>
          
          {/* Agent-specific data visualization */}
          {renderAgentSpecificData(agent)}
          
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
          className="px-4 pb-4 pt-0"
          style={{ 
            borderTop: '1px solid var(--card-border)', 
            color: 'var(--foreground)'
          }}
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

// Helper function to render agent-specific data visualizations
const renderAgentSpecificData = (agent: Agent) => {
  if (!agent.data || Object.keys(agent.data).length === 0) return null;
  
  switch (agent.id) {
    case 1: // Materials Agent
      return renderMaterialsData(agent.data);
    case 2: // Manufacturing Agent
      return renderManufacturingData(agent.data);
    case 3: // Packaging Agent
      return renderPackagingData(agent.data);
    case 4: // Transport Agent
      return renderTransportData(agent.data);
    case 5: // Lifecycle Agent
      return renderLifecycleData(agent.data);
    case 6: // End-of-Life Agent
      return renderEndOfLifeData(agent.data);
    default:
      return null;
  }
};

const renderMaterialsData = (data: Record<string, AgentData>) => {
  const materialsData = data as unknown as MaterialsData;
  
  return (
    <div className="mt-4">
      <h4 className="font-medium mb-2">Material Composition:</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
        {materialsData.materials?.map((material, index) => (
          <div 
            key={index} 
            className="p-3 rounded text-sm"
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.03)' }}
          >
            <div className="font-medium">{material.name} ({material.percentage}%)</div>
            <div className="text-xs mt-1">Carbon Intensity: {material.carbonIntensity}</div>
            <div className="text-xs">Recyclability: {material.recyclability}</div>
            <div className="text-xs">Source: {material.sourceInfo}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm mt-3">
        <div>
          <span className="font-medium">Recyclable:</span> {materialsData.totalRecyclablePercentage}%
        </div>
        <div>
          <span className="font-medium">Renewable:</span> {materialsData.materialsRenewablePercentage}%
        </div>
      </div>
    </div>
  );
};

const renderManufacturingData = (data: Record<string, AgentData>) => {
  const manufacturingData = data as unknown as ManufacturingData;
  
  return (
    <div className="mt-4">
      <h4 className="font-medium mb-2">Manufacturing Locations:</h4>
      <div className="grid grid-cols-1 gap-2 mb-3">
        {manufacturingData.manufacturingLocations?.map((location, index) => (
          <div 
            key={index} 
            className="p-3 rounded text-sm"
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.03)' }}
          >
            <div className="font-medium">{location.country}, {location.city}</div>
            <div className="text-xs mt-1">Facility: {location.facilityType}</div>
            <div className="text-xs">Energy Sources: {location.energySources.join(', ')}</div>
            <div className="text-xs">Emissions: {location.emissions}</div>
            <div className="text-xs">Certifications: {location.certifications.join(', ')}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

const renderPackagingData = (data: Record<string, AgentData>) => {
  const packagingData = data as unknown as PackagingData;
  
  return (
    <div className="mt-4">
      <h4 className="font-medium mb-2">Packaging Materials:</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
        {packagingData.packagingMaterials?.map((pkg, index) => (
          <div 
            key={index} 
            className="p-3 rounded text-sm"
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.03)' }}
          >
            <div className="font-medium">{pkg.material} ({pkg.percentage}%)</div>
            <div className="text-xs mt-1">Recyclability: {pkg.recyclability}</div>
            <div className="text-xs">Carbon Footprint: {pkg.carbonFootprint}</div>
            <div className="text-xs">Source: {pkg.sourceInfo}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm mt-3">
        <div>
          <span className="font-medium">Weight:</span> {packagingData.packagingWeight}
        </div>
        <div>
          <span className="font-medium">Biodegradable:</span> {packagingData.biodegradablePercentage}%
        </div>
      </div>
    </div>
  );
};

const renderTransportData = (data: Record<string, AgentData>) => {
  const transportData = data as unknown as TransportData;
  
  return (
    <div className="mt-4">
      <h4 className="font-medium mb-2">Shipping Routes:</h4>
      <div className="grid grid-cols-1 gap-2 mb-3">
        {transportData.primaryShippingRoutes?.map((route, index) => (
          <div 
            key={index} 
            className="p-3 rounded text-sm"
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.03)' }}
          >
            <div className="font-medium">{route.origin} → {route.destination}</div>
            <div className="text-xs mt-1">Method: {route.method}</div>
            <div className="text-xs">Distance: {route.distance}</div>
            <div className="text-xs">Emissions: {route.emissionsPerUnit}</div>
          </div>
        ))}
      </div>
      <div className="text-sm mt-3">
        <span className="font-medium">Total Transport Emissions:</span> {transportData.totalTransportEmissions}
      </div>
    </div>
  );
};

const renderLifecycleData = (data: Record<string, AgentData>) => {
  const lifecycleData = data as unknown as LifecycleData;
  
  return (
    <div className="mt-4">
      <h4 className="font-medium mb-2">Usage Impact:</h4>
      <div className="p-3 rounded text-sm mb-3" style={{ backgroundColor: 'rgba(0, 0, 0, 0.03)' }}>
        <div className="font-medium">Expected Lifespan: {lifecycleData.expectedLifespan}</div>
        <div className="text-xs mt-2">Energy Use: {lifecycleData.energyConsumption?.average}</div>
        <div className="text-xs">Annual Usage: {lifecycleData.energyConsumption?.annualUsage}</div>
        <div className="text-xs">Lifetime Energy: {lifecycleData.energyConsumption?.totalLifetimeEnergy}</div>
        <div className="text-xs">Lifetime Emissions: {lifecycleData.energyConsumption?.averageLifetimeEmissions}</div>
      </div>
      <h4 className="font-medium mb-2">Repairability:</h4>
      <div className="p-3 rounded text-sm" style={{ backgroundColor: 'rgba(0, 0, 0, 0.03)' }}>
        <div className="font-medium">Score: {lifecycleData.repairability?.score}</div>
        <div className="text-xs mt-2">Limitations:</div>
        <ul className="list-disc pl-5 text-xs">
          {lifecycleData.repairability?.limitations?.map((limitation, index) => (
            <li key={index}>{limitation}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

const renderEndOfLifeData = (data: Record<string, AgentData>) => {
  const endOfLifeData = data as unknown as EndOfLifeData;
  
  return (
    <div className="mt-4">
      <h4 className="font-medium mb-2">Recyclability:</h4>
      <div className="p-3 rounded text-sm mb-3" style={{ backgroundColor: 'rgba(0, 0, 0, 0.03)' }}>
        <div className="font-medium">{endOfLifeData.recyclability?.overallScore}</div>
        <div className="text-xs mt-2">Highly Recyclable:</div>
        <div className="flex flex-wrap gap-1 mt-1">
          {endOfLifeData.recyclability?.componentsBreakdown?.highlyRecyclable?.map((item, i) => (
            <span key={i} className="pill pill-primary">{item}</span>
          ))}
        </div>
        <div className="text-xs mt-2">Hard to Recycle:</div>
        <div className="flex flex-wrap gap-1 mt-1">
          {endOfLifeData.recyclability?.componentsBreakdown?.hardToRecycle?.map((item, i) => (
            <span key={i} className="pill pill-neutral">{item}</span>
          ))}
        </div>
      </div>
      <h4 className="font-medium mb-2">Disposal Methods:</h4>
      <div className="p-3 rounded text-sm" style={{ backgroundColor: 'rgba(0, 0, 0, 0.03)' }}>
        {Object.entries(endOfLifeData.commonDisposalMethods || {}).map(([method, percentage], index) => (
          <div key={index} className="flex justify-between mb-1">
            <span className="capitalize">{method}:</span>
            <span>{percentage}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentCard;