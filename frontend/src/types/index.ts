// ==================== AUTH & USER TYPES ====================
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  full_name: string;
  password: string;
  department_code?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserDto;
}

export interface UserDto {
  id: string;
  email: string;
  username?: string;
  full_name: string;
  phone?: string;
  position?: string;
  avatar_url?: string;
  role: 'OFFICER' | 'LEADER' | 'IT_ADMIN' | 'BIZ_ADMIN';
  department?: DepartmentDto;
  is_active: boolean;
  is_email_verified: boolean;
  last_login_at?: string;
  must_change_pw: boolean;
  timezone: string;
  language: string;
  preferences: Record<string, unknown>;
  document_quota: number;
  storage_quota_mb: number;
  created_at: string;
}

export interface DepartmentDto {
  id: string;
  name: string;
  code: string;
  parent_id?: string;
}

// ==================== DOCUMENT TYPES ====================
export interface DocumentDto {
  id: string;
  user_id: string;
  department_id?: string;
  folder_id?: string;
  original_filename: string;
  display_name: string;
  file_type: 'docx' | 'pdf';
  file_size_bytes: number;
  minio_object_key: string;
  checksum_sha256: string;
  mime_type: string;
  is_deleted: boolean;
  doc_type?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface DocumentVersionDto {
  id: string;
  document_id: string;
  version_number: number;
  version_label?: string;
  minio_object_key: string;
  file_size_bytes: number;
  checksum_sha256: string;
  change_notes?: string;
  created_by?: string;
  created_at: string;
}

export interface DocumentFolderDto {
  id: string;
  user_id: string;
  parent_id?: string;
  name: string;
  color?: string;
  icon?: string;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

// ==================== CHECK TYPES ====================
export interface CheckResultDto {
  id: string;
  document_id: string;
  version_id?: string;
  rule_set_id?: number;
  score?: number;
  total_errors: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  ai_model?: string;
  checked_at: string;
  status: 'processing' | 'completed' | 'error' | 'timeout';
  processing_time_ms?: number;
  error_message?: string;
  errors: CheckErrorDto[];
}

export interface CheckErrorDto {
  id: string;
  error_type: string;
  severity: 'critical' | 'warning' | 'info';
  description: string;
  current_value?: string;
  expected_value?: string;
  suggested_fix?: string;
  rag_reference?: string;
  location_info?: Record<string, unknown>;
  confidence?: number;
}

// ==================== KNOWLEDGE TYPES ====================
export interface KnowledgeCategoryDto {
  id: number;
  name: string;
  code: string;
  description?: string;
  sort_order: number;
  created_at: string;
}

export interface KnowledgeDocDto {
  id: string;
  category_id?: number;
  title: string;
  doc_code?: string;
  doc_type: string;
  minio_object_key: string;
  ragflow_doc_id?: string;
  chunk_count: number;
  vector_size_mb: number;
  index_status: string;
  is_active: boolean;
  effective_date?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  category?: KnowledgeCategoryDto;
}

// ==================== RULE TYPES ====================
export interface RuleSetDto {
  id: number;
  name: string;
  code: string;
  description?: string;
  doc_types: string[];
  is_default: boolean;
  is_active: boolean;
  version: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
  rules: RuleDto[];
}

export interface RuleDto {
  id: string;
  rule_set_id: number;
  rule_code: string;
  category: string;
  name: string;
  description?: string;
  check_property?: string;
  expected_value: unknown;
  tolerance?: unknown;
  severity: 'critical' | 'warning' | 'info';
  error_message: string;
  fix_suggestion?: string;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

// ==================== TEMPLATE TYPES ====================
export interface TemplateDto {
  id: number;
  template_name: string;
  template_code: string;
  description?: string;
  minio_object_key: string;
  rule_set_id: number;
  thumbnail_url?: string;
  is_active: boolean;
  version: string;
  doc_types: string[];
  download_count: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

// ==================== NOTIFICATION TYPES ====================
export interface NotificationDto {
  id: string;
  user_id?: string;
  type: string;
  channel: string;
  title: string;
  body: string;
  action_url?: string;
  priority: string;
  is_read: boolean;
  created_at: string;
}

// ==================== APPROVAL TYPES ====================
export interface ApprovalDto {
  id: string;
  document_id: string;
  check_result_id?: string;
  submitted_by: string;
  approver_id: string;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  submitter_note?: string;
  approver_note?: string;
  submitted_at: string;
  reviewed_at?: string;
  deadline_at?: string;
}

// ==================== ADMIN TYPES ====================
export interface SystemSettingDto {
  key: string;
  value?: string;
  value_type: string;
  category: string;
  label: string;
  description?: string;
  is_editable: boolean;
}

export interface AuditLogDto {
  id: number;
  user_id?: string;
  actor_type: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  ip_address?: string;
  result: string;
  created_at: string;
}

export interface ApiKeyDto {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  last_used_at?: string;
  usage_count: number;
  is_active: boolean;
  created_at: string;
}

// ==================== ANALYTICS TYPES ====================
export interface DashboardDto {
  total_documents: number;
  documents_today: number;
  pass_rate: number;
  average_score: number;
  recent_checks: Record<string, unknown>[];
  trend_data: { date: string; score: number }[];
}

// ==================== WEBSOCKET TYPES ====================
export interface WsProgressEvent {
  type: 'progress';
  check_id: string;
  stage: 'extracting' | 'rag' | 'llm' | 'done';
  percent: number;
  message: string;
}

export interface WsCompleteEvent {
  type: 'complete';
  check_id: string;
  result_id: string;
  score: number;
  total_errors: number;
}

export interface WsNotificationEvent {
  type: 'notification';
  notification: NotificationDto;
}

export type WsEvent = WsProgressEvent | WsCompleteEvent | WsNotificationEvent;