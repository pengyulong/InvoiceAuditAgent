// 通用响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp: string
}

// 分页请求类型
export interface PaginationParams {
  page: number
  pageSize: number
}

// 分页响应类型
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 文件上传类型
export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

// Agent状态类型
export type AgentStatus = 'idle' | 'running' | 'completed' | 'error'

// Agent信息类型
export interface AgentInfo {
  name: string
  status: AgentStatus
  progress: number
  message?: string
  startTime?: Date
  endTime?: Date
}

// 审计配置类型
export interface AuditConfig {
  enableDuplicateDetection: boolean
  enableAmountValidation: boolean
  enableContentMatching: boolean
  confidenceThreshold: number
}

// 问题严重程度
export type IssueSeverity = 'low' | 'medium' | 'high' | 'critical'

// 问题类型
export type IssueType = 'duplicate' | 'amount_mismatch' | 'content_mismatch' | 'missing_info' | 'calculation_error'

// 导出格式
export type ExportFormat = 'pdf' | 'excel' | 'json' | 'csv'

// 主题类型
export type Theme = 'light' | 'dark' | 'auto'

// 语言类型
export type Language = 'zh-CN' | 'en-US'

// 文件类型
export type FileType = 'application/pdf' | 'image/jpeg' | 'image/png' | 'application/zip'

// 排序方向
export type SortDirection = 'asc' | 'desc'

// 表格列配置
export interface TableColumn {
  key: string
  label: string
  width?: number
  sortable?: boolean
  filterable?: boolean
}

// 过滤器配置
export interface FilterConfig {
  key: string
  label: string
  type: 'select' | 'date' | 'text' | 'number'
  options?: Array<{ label: string; value: any }>
}

// 图表数据类型
export interface ChartData {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    backgroundColor?: string[]
    borderColor?: string[]
  }>
}

// 统计数据类型
export interface Statistics {
  totalAudits: number
  completedAudits: number
  failedAudits: number
  averageProcessingTime: number
  totalAmountProcessed: number
  issuesFound: number
}