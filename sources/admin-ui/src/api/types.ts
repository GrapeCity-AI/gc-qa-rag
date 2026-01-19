// API Response Types

export interface ApiError {
  code: string
  message: string
  field?: string
  details?: Record<string, unknown>
}

export interface ApiResponse<T> {
  data: T | null
  meta?: Record<string, unknown>
  errors: ApiError[]
}

export interface PaginationMeta {
  page: number
  page_size: number
  total_items: number
  total_pages: number
}

export interface PaginatedResponse<T> {
  data: T[]
  meta: PaginationMeta
  errors: ApiError[]
}

// Health & Stats
export interface HealthStatus {
  status: string
  version: string
  timestamp: string
  components: Record<string, string>
}

export interface CountStats {
  knowledge_bases: number
  versions: number
  pending_tasks: number
  running_tasks: number
  completed_tasks: number
  failed_tasks: number
}

// Knowledge Base
export interface KnowledgeBase {
  id: string
  name: string
  description: string
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
  version_count: number
  latest_version: string | null
}

export interface KnowledgeBaseSummary {
  id: string
  name: string
  description: string
  version_count: number
  latest_version: string | null
  created_at: string
  updated_at: string
}

export interface KnowledgeBaseCreate {
  name: string
  description?: string
  metadata?: Record<string, unknown>
}

export interface KnowledgeBaseUpdate {
  name?: string
  description?: string
  metadata?: Record<string, unknown>
}

// Version
export interface Version {
  id: string
  knowledge_base_id: string
  version_tag: string
  status: string
  parent_version_id: string | null
  created_at: string
  published_at: string | null
  metadata: Record<string, unknown>
  file_count: number
  indexed_count: number
  pending_count: number
  failed_count: number
}

export interface VersionSummary {
  id: string
  version_tag: string
  status: string
  file_count: number
  created_at: string
}

export interface VersionCreate {
  version_tag: string
  parent_version_id?: string
  metadata?: Record<string, unknown>
}

export interface VersionBuildRequest {
  build_type: 'full' | 'incremental'
  pipeline_config?: PipelineStepConfig[]
}

export interface VersionPublishRequest {
  target_environment_id: string
  alias_name?: string
  publish_strategy?: 'replace' | 'blue_green'
  include_raw_files?: boolean
}

export interface VersionIngestRequest {
  connector_type: string
  source_config: Record<string, unknown>
  incremental?: boolean
  dedup_strategy?: 'skip' | 'replace' | 'version'
}

export interface PipelineStepConfig {
  step_type: string
  config?: Record<string, unknown>
  enabled?: boolean
}

export interface FileVersion {
  id: string
  raw_file_id: string
  knowledge_base_version_id: string
  content_hash: string
  index_status: string
  indexed_at: string | null
  created_at: string
  source_type: string | null
  source_uri: string | null
  original_name: string | null
  mime_type: string | null
  size_bytes: number | null
}

// Task
export interface Task {
  id: string
  task_type: string
  knowledge_base_id: string
  knowledge_base_version_id: string
  status: string
  priority: number
  retry_count: number
  max_retries: number
  created_at: string
  started_at: string | null
  completed_at: string | null
  metadata: Record<string, unknown>
  knowledge_base_name: string | null
  version_tag: string | null
  duration_seconds: number | null
}

export interface TaskSummary {
  id: string
  task_type: string
  status: string
  knowledge_base_name: string | null
  version_tag: string | null
  created_at: string
  completed_at: string | null
}

export interface ProcessingError {
  item_id: string
  item_name: string
  step: string
  error_type: string
  error_message: string
  stacktrace: string | null
  timestamp: string
  recoverable: boolean
}

export interface StepStats {
  step_type: string
  input_count: number
  output_count: number
  duration_seconds: number
  errors_count: number
  success_rate: number
}

export interface TaskResult {
  task_id: string
  task_type: string
  status: string
  total_items: number
  succeeded_count: number
  failed_count: number
  skipped_count: number
  errors: ProcessingError[]
  started_at: string
  completed_at: string
  duration_seconds: number
  success_rate: number
  step_stats: Record<string, StepStats>
  index_records_count: number
  new_files_count: number
  updated_files_count: number
  unchanged_files_count: number
  target_collection: string | null
  alias_applied: string | null
}

export interface TaskCancelRequest {
  reason?: string
}

export interface TaskRetryRequest {
  reset_retry_count?: boolean
  priority?: number
}

// Connector
export interface ConnectorType {
  type: string
  name: string
  description: string
  config_schema: Record<string, unknown>
}

export interface ConnectorTestRequest {
  connector_type: string
  config: Record<string, unknown>
}

export interface ConnectorTestResponse {
  success: boolean
  message: string
  details: Record<string, unknown>
}

// WebSocket Message
export interface TaskProgressUpdate {
  task_id: string
  event_type: string
  status: string
  progress?: number
  message?: string
  current_step?: string
  items_processed?: number
  total_items?: number
  timestamp: string
}
