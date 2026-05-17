export interface CheckResult {
  id: string;
  document_id: string;
  score: number | null;
  total_errors: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  ai_model?: string;
  checked_at: string;
  status: string;
  processing_time_ms?: number;
  errors: CheckError[];
}

export interface CheckError {
  id: string;
  error_type: string;
  severity: 'critical' | 'warning' | 'info';
  description: string;
  current_value?: string;
  expected_value?: string;
  suggested_fix?: string;
  rag_reference?: string;
  location_info?: { page?: number; paragraph?: number };
  confidence?: number;
}