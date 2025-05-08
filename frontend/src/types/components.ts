/**
 * Shared component interface definitions
 */

export interface StreamingTextProps {
  url?: string;
  isStreaming: boolean;
  productUrl?: string;
  onStreamingComplete?: () => void;
}

export interface ProductInputProps {
  onSubmit: (input: string) => void;
  isLoading?: boolean;
}

export interface AgentData {
  messages: Array<{type: string, content: string}>;
  summary: string;
  carbon: number | null;
  isCompleted: boolean;
}

export interface FootprintAnalysisProps {
  url?: string;
  isStreaming: boolean;
  productUrl?: string;
  onStreamingComplete?: () => void;
}

export interface AgentSectionProps {
  title?: string;
  icon?: string;
  agentKey: string;
  summary?: string;
  content: React.ReactNode;
  isCompleted?: boolean;
  carbon?: number;
  borderColor?: string;
  bgColor?: string;
  textColor?: string;
}