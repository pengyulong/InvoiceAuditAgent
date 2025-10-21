import { apiGet, apiPost } from './api'
import type {
  ApiResponse,
  AuditTask,
  AuditReport,
  FileInfo,
  AuditConfig
} from '@/types'

// 上传相关API
export const uploadZipFile = (file: File, onProgress?: (percent: number) => void): Promise<ApiResponse<{
  task_id: string
  file_name: string
  file_size: number
  extracted_files: FileInfo[]
  total_files: number
}>> => {
  const formData = new FormData()
  formData.append('file', file)

  return apiPost('/upload/zip', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percent)
      }
    }
  })
}

export const uploadContractFile = (taskId: string, file: File): Promise<ApiResponse<{
  file_id: string
  file_name: string
  file_path: string
  file_size: number
}>> => {
  const formData = new FormData()
  formData.append('task_id', taskId)
  formData.append('file', file)

  return apiPost('/upload/contract', formData)
}

export const uploadInvoiceFiles = (taskId: string, files: File[]): Promise<ApiResponse<{
  task_id: string
  uploaded_files: any[]
  total_count: number
}>> => {
  const formData = new FormData()
  formData.append('task_id', taskId)

  files.forEach(file => {
    formData.append('files', file)
  })

  return apiPost('/upload/invoices', formData)
}

export const getTaskFiles = (taskId: string): Promise<ApiResponse<{
  task_id: string
  files: FileInfo[]
  total_count: number
}>> => {
  return apiGet(`/upload/files/${taskId}`)
}

// 审计相关API
export const startAudit = (taskId: string, config?: AuditConfig): Promise<ApiResponse<{
  audit_id: string
  status: string
  message: string
}>> => {
  return apiPost('/audit/start', {
    task_id: taskId,
    audit_config: config || {}
  })
}

export const getAuditStatus = (auditId: string): Promise<ApiResponse<{
  audit_id: string
  status: string
  progress: number
  current_step: string
  processed_files: number
  total_files: number
  error_message?: string
  created_at?: string
  completed_at?: string
}>> => {
  return apiGet(`/audit/${auditId}/status`)
}

export const getAuditResults = (auditId: string): Promise<ApiResponse<AuditReport>> => {
  return apiGet(`/audit/${auditId}/results`)
}

export const stopAudit = (auditId: string): Promise<ApiResponse<{
  audit_id: string
  status: string
}>> => {
  return apiPost(`/audit/${auditId}/stop`)
}

export const getAuditTasks = (
  status?: string,
  limit: number = 20,
  offset: number = 0
): Promise<ApiResponse<{
  tasks: AuditTask[]
  total: number
  limit: number
  offset: number
}>> => {
  const params: any = { limit, offset }
  if (status) {
    params.status = status
  }
  return apiGet('/audit/tasks', params)
}

// 结果相关API
export const exportReport = (auditId: string, format: 'pdf' | 'excel' | 'json'): Promise<Blob> => {
  return apiGet(`/results/${auditId}/export?format=${format}`, {}, {
    responseType: 'blob'
  })
}

export const getReportSummary = (auditId: string): Promise<ApiResponse<{
  summary: any
  charts: any
}>> => {
  return apiGet(`/results/${auditId}/summary`)
}