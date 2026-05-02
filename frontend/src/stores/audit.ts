import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface FileInfo {
  id: string
  name: string
  size: number
  type: string
  category: 'contract' | 'invoice' | 'other'
  path?: string
  url?: string
}

export interface AuditTask {
  id: string
  name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  files: FileInfo[]
  createdAt: Date
  completedAt?: Date
  errorMessage?: string
}

export interface AuditResult {
  id: string
  taskId: string
  status: 'pass' | 'fail' | 'warning'
  summary: {
    contractAmount: number
    invoiceTotal: number
    coverage: number
    issueCount: number
    processingTime: number
  }
  contractInfo?: {
    contractNumber: string
    buyerName: string
    sellerName: string
    totalAmount: number
    taxRate: number
    items: Array<{
      name: string
      quantity: number
      unitPrice: number
    }>
  }
  invoices?: Array<{
    id: string
    invoiceNumber: string
    amount: number
    taxAmount: number
    status: 'normal' | 'duplicate' | 'error'
    confidence: number
  }>
  issues?: Array<{
    id: string
    type: 'error' | 'warning' | 'info'
    severity: 'high' | 'medium' | 'low'
    title: string
    description: string
    recommendation: string
  }>
  comparisons?: Array<{
    productName: string
    contractQuantity: number
    invoiceQuantity: number
    difference: number
    status: 'match' | 'mismatch' | 'partial'
  }>
}

export const useAuditStore = defineStore('audit', () => {
  // 状态
  const currentTask = ref<AuditTask | null>(null)
  const auditHistory = ref<AuditTask[]>([])
  const currentResult = ref<AuditResult | null>(null)
  const wsConnection = ref<WebSocket | null>(null)

  // 计算属性
  const hasActiveTask = computed(() => currentTask.value !== null)
  const isProcessing = computed(() => currentTask.value?.status === 'processing')
  const progressPercentage = computed(() => currentTask.value?.progress || 0)

  // 方法
  const createTask = (name: string, files: FileInfo[]): AuditTask => {
    const task: AuditTask = {
      id: generateId(),
      name,
      status: 'pending',
      progress: 0,
      files,
      createdAt: new Date()
    }

    currentTask.value = task
    auditHistory.value.unshift(task)
    return task
  }

  const updateTaskStatus = (
    taskId: string,
    status: AuditTask['status'],
    progress?: number,
    errorMessage?: string
  ) => {
    if (currentTask.value?.id === taskId) {
      currentTask.value.status = status
      if (progress !== undefined) {
        currentTask.value.progress = progress
      }
      if (errorMessage) {
        currentTask.value.errorMessage = errorMessage
      }
      if (status === 'completed') {
        currentTask.value.completedAt = new Date()
      }
    }

    // 更新历史记录
    const historyTask = auditHistory.value.find(t => t.id === taskId)
    if (historyTask) {
      historyTask.status = status
      if (progress !== undefined) {
        historyTask.progress = progress
      }
      if (errorMessage) {
        historyTask.errorMessage = errorMessage
      }
      if (status === 'completed') {
        historyTask.completedAt = new Date()
      }
    }
  }

  const setCurrentResult = (result: AuditResult) => {
    currentResult.value = result
  }

  const clearCurrentTask = () => {
    currentTask.value = null
  }

  const clearCurrentResult = () => {
    currentResult.value = null
  }

  const connectWebSocket = (taskId: string) => {
    if (wsConnection.value) {
      wsConnection.value.close()
    }

    const wsUrl = `ws://127.0.0.1:8000/ws/audit/${taskId}`
    wsConnection.value = new WebSocket(wsUrl)

    wsConnection.value.onopen = () => {
      console.log('WebSocket connected')
    }

    wsConnection.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'progress') {
          updateTaskStatus(taskId, 'processing', data.progress)
        } else if (data.type === 'completed') {
          updateTaskStatus(taskId, 'completed', 100)
        } else if (data.type === 'error') {
          updateTaskStatus(taskId, 'failed', undefined, data.message)
        }
      } catch (error) {
        console.error('WebSocket message error:', error)
      }
    }

    wsConnection.value.onclose = () => {
      console.log('WebSocket disconnected')
    }

    wsConnection.value.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  const disconnectWebSocket = () => {
    if (wsConnection.value) {
      wsConnection.value.close()
      wsConnection.value = null
    }
  }

  // 辅助函数
  const generateId = (): string => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
  }

  return {
    // 状态
    currentTask,
    auditHistory,
    currentResult,
    wsConnection,
    // 计算属性
    hasActiveTask,
    isProcessing,
    progressPercentage,
    // 方法
    createTask,
    updateTaskStatus,
    setCurrentResult,
    clearCurrentTask,
    clearCurrentResult,
    connectWebSocket,
    disconnectWebSocket
  }
})
