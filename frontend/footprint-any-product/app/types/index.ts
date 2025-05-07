// Shared types for the application

// Basic agent data type for recursive type definition
export interface AgentData {
  [key: string]: string | number | boolean | null | AgentData | AgentData[] | unknown;
}

// Basic agent interface
export interface Agent {
  id: number;
  name: string;
  status: string;
  carbonScore: number;
  details?: string;
  timestamp?: string;
  data?: Record<string, AgentData>;
}

// API response interface
export interface ApiResponse {
  request_id: string;
  timestamp: string;
  product_url: string;
  status: string;
  agents: Agent[];
  product_name?: string;
}

// For history page
export interface HistoryResult {
  id: string;
  product_url: string;
  timestamp: string; 
  status: string;
  overall_score: number;
  product_name?: string;
}

// Debug info for database connection
export interface DebugInfo {
  connection?: string;
  test?: unknown;
  tables?: string[];
  analysis_results_count?: number;
  error?: string;
}

// Database-related interfaces
export interface AnalysisResult {
  id: string;
  product_url: string;
  product_name?: string;
  timestamp: string;
  status: string;
  overall_score: number;
  request_data?: Record<string, unknown>;
}

export interface AnalysisAgent {
  id: number;
  result_id: string;
  agent_id: number;
  name: string;
  status: string;
  carbon_score: number;
  details?: string;
  agent_timestamp?: string;
  data?: Record<string, unknown>;
}

export interface FormattedAgent {
  id: number;
  name: string;
  status: string;
  carbonScore: number;
  details?: string;
  timestamp?: string;
  data?: Record<string, unknown>;
}

export interface FullAnalysisResult extends AnalysisResult {
  agents: FormattedAgent[];
}

// Agent-specific data types for visualization
export interface MaterialInfo {
  name: string;
  percentage: number;
  carbonIntensity: string;
  recyclability: string;
  sourceInfo: string;
}

export interface MaterialsData {
  materials?: MaterialInfo[];
  totalRecyclablePercentage?: number;
  materialsRenewablePercentage?: number;
}

export interface ManufacturingLocation {
  country: string;
  city: string;
  facilityType: string;
  energySources: string[];
  emissions: string;
  certifications: string[];
}

export interface ManufacturingData {
  manufacturingLocations?: ManufacturingLocation[];
}

export interface PackagingMaterial {
  material: string;
  percentage: number;
  recyclability: string;
  carbonFootprint: string;
  sourceInfo: string;
}

export interface PackagingData {
  packagingMaterials?: PackagingMaterial[];
  packagingWeight?: string;
  biodegradablePercentage?: number;
}

export interface ShippingRoute {
  origin: string;
  destination: string;
  method: string;
  distance: string;
  emissionsPerUnit: string;
}

export interface TransportData {
  primaryShippingRoutes?: ShippingRoute[];
  totalTransportEmissions?: string;
}

export interface EnergyConsumption {
  average: string;
  annualUsage: string;
  totalLifetimeEnergy: string;
  averageLifetimeEmissions: string;
}

export interface Repairability {
  score: string;
  limitations?: string[];
}

export interface LifecycleData {
  expectedLifespan?: string;
  energyConsumption?: EnergyConsumption;
  repairability?: Repairability;
}

export interface RecyclabilityInfo {
  overallScore: string;
  componentsBreakdown?: {
    highlyRecyclable?: string[];
    hardToRecycle?: string[];
  };
}

export interface EndOfLifeData {
  recyclability?: RecyclabilityInfo;
  commonDisposalMethods?: Record<string, string>;
}

// Summary agent specific types
export interface SummaryData {
  totalCarbonFootprint?: {
    score: number;
    classification: string;
    breakdown: Record<string, { score: number; contribution: string; }>;
    comparativeRanking: string;
  };
  keyImpactAreas?: string[];
  positiveSustainabilityAspects?: string[];
  consumerRecommendation?: string;
  sustainabilityImprovementPotential?: string;
  similarProductsWithBetterScores?: string[];
  improvementRecommendations?: string[];
}

export interface SummaryAgent {
  id: number;
  name: string;
  status: string;
  carbonScore: number;
  details?: string;
  timestamp?: string;
  data?: SummaryData;
}

// Component-specific interfaces
export interface AgentCardProps {
  agent: Agent;
  isExpanded: boolean;
  showRawJson: boolean;
  onToggleDetails: () => void;
  onToggleRawJson: () => void;
  index: number;
}

export interface SummaryCardProps {
  agent: SummaryAgent;
  isExpanded: boolean;
  showRawJson: boolean;
  onToggleDetails: () => void;
  onToggleRawJson: () => void;
}

export interface CarbonScoreProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  animated?: boolean;
}

export interface StatusIndicatorProps {
  status: string;
  compact?: boolean;
}

// Pagination props
export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

// Search filters props
export interface SearchFiltersProps {
  onSearch: (searchTerm: string) => void;
  onScoreFilterChange: (minScore: number, maxScore: number) => void;
  onDateFilterChange: (startDate: string | null, endDate: string | null) => void;
}

// Results table props
export interface ResultsTableProps {
  results: HistoryResult[];
  isLoading: boolean;
  error: string | null;
}

// Muir API related types
export interface MuirApiResponse {
  data: unknown | null;
  error?: string;
  isLoading: boolean;
}

// Material breakdown component type for Muir API
export interface MaterialComponent {
  component: string;
  mass: number;
  recycledContent: number;
}

// New run data structure for Muir API
export interface NewRunData {
  product_name: string;
  product_description: string;
  mass_kg: number;
  source_location: string;
  destination_location: string;
  upstream_sourcing_countries: string[];
  material_breakdown: {
    product: string;
    productMass: number;
    massUnit: string;
    components: MaterialComponent[];
  };
  supplier_scope_1_and_2_ef: number;
}

// Muir API request type
export type MuirApiRequestType = 'info' | 'runs' | 'run-by-id' | 'procurement-ids' | 'procurement' | 'create-run';