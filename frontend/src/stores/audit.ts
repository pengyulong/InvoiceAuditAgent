import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAuditTasks, startAudit as startAuditApi } from '@/services/audit'
import { apiGet } from '@/services/api'
import type {
  AuditTask,
  AuditReport,
  WebSocketMessage,
  ProgressMessage,
  Statistics
} from '@/types'

export const useAuditStore = defineStore('audit', () => {
  // 状态
  const currentTask = ref<AuditTask | null>(null)
  const auditReport = ref<AuditReport | null>(null)
  const auditProgress = ref(0)
  const currentStep = ref('')
  const wsConnection = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const errorMessage = ref('')

  // 计算属性
  const isProcessing = computed(() =>
    currentTask.value?.status === 'processing'
  )

  const isCompleted = computed(() =>
    currentTask.value?.status === 'completed'
  )

  const hasError = computed(() =>
    currentTask.value?.status === 'failed' || !!errorMessage.value
  )

  const progressPercentage = computed(() =>
    currentTask.value?.progress_percentage || 0
  )

  const statistics = computed<Statistics>(() => {
    if (!auditReport.value) {
      return {
        contracts_analyzed: 0,
        invoices_analyzed: 0,
        issues_found: 0,
        total_files: 0
      }
    }

    return {
      contracts_analyzed: auditReport.value.contracts.length,
      invoices_analyzed: auditReport.value.invoices.length,
      issues_found: auditReport.value.issues_summary.total_issues,
      total_files: auditReport.value.contracts.length + auditReport.value.invoices.length
    }
  })

  // 方法
  const setCurrentTask = (task: AuditTask | null) => {
    currentTask.value = task
  }

  const setAuditReport = (report: AuditReport | null) => {
    auditReport.value = report
  }

  const updateProgress = (progress: number, step: string) => {
    auditProgress.value = progress
    currentStep.value = step

    if (currentTask.value) {
      currentTask.value.progress_percentage = progress
      currentTask.value.current_step = step
    }
  }

  const setErrorMessage = (message: string) => {
    errorMessage.value = message
  }

  const clearError = () => {
    errorMessage.value = ''
  }

  const connectWebSocket = (auditId: string) => {
    if (wsConnection.value) {
      wsConnection.value.close()
    }

    const wsUrl = `ws://localhost:8000/ws/audit/${auditId}`
    wsConnection.value = new WebSocket(wsUrl)

    wsConnection.value.onopen = () => {
      console.log('WebSocket连接已建立')
      isConnected.value = true
      clearError()
    }

    wsConnection.value.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        handleWebSocketMessage(message)
      } catch (error) {
        console.error('解析WebSocket消息失败:', error)
      }
    }

    wsConnection.value.onerror = (error) => {
      console.error('WebSocket连接错误:', error)
      isConnected.value = false
      setErrorMessage('WebSocket连接失败')
    }

    wsConnection.value.onclose = () => {
      console.log('WebSocket连接已关闭')
      isConnected.value = false
    }
  }

  const disconnectWebSocket = () => {
    if (wsConnection.value) {
      wsConnection.value.close()
      wsConnection.value = null
    }
    isConnected.value = false
  }

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    console.log('收到WebSocket消息:', message)

    switch (message.type) {
      case 'connection_established':
        console.log('WebSocket连接确认:', message.data.message)
        break

      case 'progress':
        handleProgressMessage(message.data as ProgressMessage)
        break

      case 'error':
        setErrorMessage(message.data.error_message)
        break

      case 'agent_update':
        console.log('Agent状态更新:', message.data)
        break

      case 'file_processed':
        console.log('文件处理完成:', message.data)
        break

      case 'audit_completed':
        handleAuditCompleted(message.data)
        break

      case 'duplicate_invoices_detected':
        console.log('检测到重复发票:', message.data)
        break

      default:
        console.log('未知消息类型:', message.type)
    }
  }

  const handleProgressMessage = (data: ProgressMessage) => {
    updateProgress(data.progress, data.step)
    console.log(`审计进度: ${data.progress}% - ${data.message}`)
  }

  const handleAuditCompleted = (data: any) => {
    if (data.report) {
      setAuditReport(data.report)
    }

    if (currentTask.value) {
      currentTask.value.status = 'completed'
      currentTask.value.progress_percentage = 100
      currentTask.value.current_step = '审计完成'
    }

    console.log('审计完成:', data)
  }

  const getRecentTasks = async (limit: number = 5): Promise<AuditTask[]> => {
    try {
      const response = await getAuditTasks(undefined, limit, 0)
      return response.data.tasks || []
    } catch (error) {
      console.error('获取最近任务失败:', error)
      return []
    }
  }

  const getTask = async (taskId: string): Promise<AuditTask | null> => {
    try {
      const response = await getAuditTasks(undefined, 1, 0)
      const tasks = response.data.tasks || []
      return tasks.find(task => task.id === taskId) || null
    } catch (error) {
      console.error('获取任务失败:', error)
      return null
    }
  }

  const getTasks = async (status?: string, limit: number = 20, offset: number = 0) => {
    try {
      const response = await getAuditTasks(status, limit, offset)
      return response.data
    } catch (error) {
      console.error('获取任务列表失败:', error)
      return { tasks: [], total: 0, page: 1, size: limit, pages: 0 }
    }
  }

  const getStatistics = async () => {
    try {
      // 使用fetch API
      const response = await fetch('/api/v1/results/statistics')
      const data = await response.json()
      return data
    } catch (error) {
      console.error('获取统计数据失败:', error)
      return {
        total_tasks: 0,
        completed_tasks: 0,
        failed_tasks: 0,
        processing_tasks: 0,
        total_contracts: 0,
        total_invoices: 0,
        success_rate: 0.0
      }
    }
  }

  const startAudit = async (taskId: string, config?: any) => {
    try {
      const response = await startAuditApi(taskId, config)
      if (response.code === 200) {
        // 更新当前任务状态
        if (currentTask.value) {
          currentTask.value.status = 'processing'
          currentTask.value.current_step = '开始审计'
          // 存储audit ID
          if (response.data?.audit_id) {
            currentTask.value.audit_id = response.data.audit_id
          }
        }
        return response.data?.audit_id || true
      } else {
        setErrorMessage(response.message || '启动审计失败')
        return false
      }
    } catch (error: any) {
      console.error('启动审计失败:', error)
      setErrorMessage(error.message || '启动审计失败')
      return false
    }
  }

  const reset = () => {
    currentTask.value = null
    auditReport.value = null
    auditProgress.value = 0
    currentStep.value = ''
    errorMessage.value = ''
    disconnectWebSocket()
  }

  return {
    // 状态
    currentTask,
    auditReport,
    auditProgress,
    currentStep,
    wsConnection,
    isConnected,
    errorMessage,

    // 计算属性
    isProcessing,
    isCompleted,
    hasError,
    progressPercentage,
    statistics,

    // 方法
    setCurrentTask,
    setAuditReport,
    updateProgress,
    setErrorMessage,
    clearError,
    connectWebSocket,
    disconnectWebSocket,
    getRecentTasks,
    getTask,
    getTasks,
    getStatistics,
    startAudit,
    reset
  }
})