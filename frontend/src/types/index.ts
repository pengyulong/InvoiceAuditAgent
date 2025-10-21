// API响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp?: string
}

// 审计任务类型
export interface AuditTask {
  id: string
  task_name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress_percentage: number
  current_step?: string
  total_files: number
  processed_files: number
  created_at: string
  completed_at?: string
  error_message?: string
  audit_id?: string
}

// 文件信息类型
export interface FileInfo {
  file_id: string
  file_name: string
  file_path: string
  file_size: number
  file_type: 'contract' | 'invoice'
  file_ext: string
}

// 提取数据类型
export interface ExtractedData {
  contract_number?: string
  buyer_name?: string
  seller_name?: string
  total_amount?: number
  tax_rate?: number
  contract_date?: string
  invoice_code?: string
  invoice_number?: string
  tax_amount?: number
  invoice_date?: string
  items?: ExtractedItem[]
}

// 商品明细类型
export interface ExtractedItem {
  item_name?: string
  specification?: string
  quantity?: number
  unit_price?: number
  total_price?: number
  tax_rate?: number
}

// 验证结果类型
export interface ValidationResult {
  validation_status: 'passed' | 'warning' | 'error'
  validation_errors: string[]
  warnings: string[]
  error_count: number
  warning_count: number
}

// 分析结果类型
export interface AnalysisResult {
  file_path: string
  success: boolean
  error?: string
  extracted_data: ExtractedData
  confidence_score: number
  validation_result: ValidationResult
  raw_response?: string
}

// 问题类型
export interface Issue {
  type: string
  severity: 'high' | 'medium' | 'low'
  description: string
  affected_items: string[]
}

// 交叉验证结果类型
export interface ValidationResult {
  overall_status: '通过' | '不通过' | '需人工复核'
  match_score: number
  issues: Issue[]
  summary: string
}

// 审计报告类型
export interface AuditReport {
  task_id: string
  audit_summary: {
    overall_status: string
    match_score: number
    contract_total_amount: number
    invoice_total_amount: number
    amount_difference: number
    total_contracts: number
    total_invoices: number
  }
  issues_summary: {
    total_issues: number
    high_priority: number
    medium_priority: number
    low_priority: number
  }
  contracts: AnalysisResult[]
  invoices: AnalysisResult[]
  validation_results: ValidationResult
  recommendations: string[]
  generated_at: string
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'progress' | 'error' | 'agent_update' | 'file_processed' | 'audit_completed' | 'connection_established' | 'duplicate_invoices_detected'
  data: any
  timestamp?: number
}

// 进度消息类型
export interface ProgressMessage {
  step: string
  progress: number
  message: string
  audit_id?: string
}

// Agent更新消息类型
export interface AgentUpdateMessage {
  agent_name: string
  status: string
  details: any
  audit_id?: string
}

// 文件处理消息类型
export interface FileProcessedMessage {
  file_info: FileInfo
  file_type: string
  status: string
  extracted_data: ExtractedData
  audit_id?: string
}

// 审计配置类型
export interface AuditConfig {
  enable_duplicate_detection?: boolean
  strict_amount_validation?: boolean
  confidence_threshold?: number
  custom_rules?: string[]
}

// 统计数据类型
export interface Statistics {
  contracts_analyzed: number
  invoices_analyzed: number
  issues_found: number
  total_files: number
  processing_time?: number
  success_rate?: number
}