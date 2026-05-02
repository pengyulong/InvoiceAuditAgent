<template>
  <div class="processing-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: '/audit/upload' }">审计管理</el-breadcrumb-item>
        <el-breadcrumb-item>审计进度</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="header-content">
        <h1 class="page-title">审计进度</h1>
        <p class="page-description">实时监控AI Agent工作流程</p>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 状态卡片 -->
      <el-card class="status-card" shadow="hover">
        <div class="status-content">
          <div class="status-info">
            <div class="status-item">
              <span class="status-label">任务ID:</span>
              <span class="status-value">{{ taskId || 'N/A' }}</span>
            </div>
            <div class="status-item">
              <span class="status-label">状态:</span>
              <el-tag :type="getStatusType(auditStatus)" size="large">
                {{ getStatusLabel(auditStatus) }}
              </el-tag>
            </div>
            <div class="status-item" v-if="auditStatus === 'processing'">
              <span class="status-label">已耗时:</span>
              <span class="status-value">{{ formatDuration(elapsedSeconds) }}</span>
            </div>
          </div>

          <!-- 整体进度条 -->
          <div class="progress-section">
            <div class="progress-header">
              <span class="progress-label">整体进度</span>
              <span class="progress-value">{{ progressPercentage }}%</span>
            </div>
            <el-progress
              :percentage="progressPercentage"
              :stroke-width="12"
              :status="getProgressStatus()"
              class="main-progress"
            />
          </div>
        </div>
      </el-card>

      <!-- Agent工作流可视化 -->
      <el-card class="workflow-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="header-icon">⚙️</span>
            <span class="header-title">Agent工作流程</span>
          </div>
        </template>

        <div class="workflow-content">
          <!-- 工作流步骤图 -->
          <div class="workflow-steps">
            <div class="steps-container">
              <div
                v-for="(step, index) in workflowSteps"
                :key="step.id"
                class="step-item"
                :class="getStepClass(step.status)"
              >
                <div class="step-icon">
                  <span v-if="step.status === 'completed'">✅</span>
                  <span v-else-if="step.status === 'running'" class="rotating">⏳</span>
                  <span v-else-if="step.status === 'error'">❌</span>
                  <span v-else>🕐</span>
                </div>
                <div class="step-content">
                  <h4 class="step-title">{{ step.title }}</h4>
                  <p class="step-description">{{ step.description }}</p>
                  <div v-if="step.status === 'running'" class="step-progress">
                    <el-progress
                      :percentage="step.progress || 0"
                      :stroke-width="4"
                      status="success"
                    />
                  </div>
                </div>
                <div v-if="index < workflowSteps.length - 1" class="step-connector" :class="getConnectorClass(step.status)"></div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 实时日志 - 全宽显示 -->
      <el-card class="logs-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><Document /></el-icon>
            <span class="header-title">实时日志</span>
            <div class="header-actions">
              <el-button
                size="small"
                :icon="Refresh"
                @click="clearLogs"
              >
                清空
              </el-button>
              <el-button
                size="small"
                :icon="Download"
                @click="downloadLogs"
              >
                导出
              </el-button>
            </div>
          </div>
        </template>

        <div class="logs-content" ref="logsContainer">
          <div class="log-entries">
            <div v-if="logs.length === 0 && auditStatus === 'processing'" class="log-placeholder">
              <span class="log-waiting-icon rotating">⏳</span>
              <span class="log-waiting-text">等待审计输出...</span>
            </div>
            <div
              v-for="(log, index) in logs"
              :key="index"
              class="log-entry"
              :class="getLogClass(log.level)"
            >
              <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
              <el-icon class="log-icon">
                <component :is="getLogIcon(log.level)" />
              </el-icon>
              <span class="log-message">{{ log.message }}</span>
            </div>
            <div ref="logBottom" class="log-bottom"></div>
          </div>
        </div>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-section">
        <el-card class="action-card" shadow="hover">
          <div class="action-content">
            <div class="action-buttons">
              <el-button
                v-if="auditStatus === 'processing'"
                type="warning"
                :icon="VideoPause"
                @click="pauseAudit"
                :loading="isPausing"
              >
                暂停审计
              </el-button>

              <el-button
                v-if="auditStatus === 'paused'"
                type="primary"
                :icon="VideoPlay"
                @click="resumeAudit"
                :loading="isResuming"
              >
                恢复审计
              </el-button>

              <el-button
                v-if="auditStatus !== 'completed'"
                type="danger"
                :icon="Close"
                @click="cancelAudit"
                :loading="isCancelling"
              >
                取消审计
              </el-button>

              <el-button
                v-if="auditStatus === 'completed'"
                type="primary"
                :icon="View"
                @click="viewResults"
              >
                查看结果
              </el-button>

              <el-button
                :icon="RefreshLeft"
                @click="goBack"
              >
                返回上传
              </el-button>
            </div>

            <!-- 统计信息 -->
            <div class="stats-section">
              <div class="stat-item">
                <span class="stat-label">处理文件:</span>
                <span class="stat-value">{{ processedFiles }}/{{ totalFiles }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">处理时间:</span>
                <span class="stat-value">{{ formatDuration(processingTime) }}</span>
              </div>
              <div class="stat-item" v-if="confidenceScore">
                <span class="stat-label">置信度:</span>
                <span class="stat-value">{{ (confidenceScore * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Close,
  Warning,
  Refresh,
  Download,
  VideoPause,
  VideoPlay,
  View,
  RefreshLeft,
  InfoFilled,
  SuccessFilled
} from '@element-plus/icons-vue'
import { useAuditStore } from '@/stores/audit'
import { apiService, authStorage } from '@/services/api'

interface StepChangeData {
  previous_step_id?: string | null
  next_step_id?: string | null
  step_name?: string
  message?: string
}

const router = useRouter()
const route = useRoute()
const auditStore = useAuditStore()

// 响应式数据
const taskId = ref(route.params.taskId as string)
const auditStatus = ref<'pending' | 'processing' | 'completed' | 'failed' | 'paused' | 'cancelled'>('pending')
const progressPercentage = ref(0)
const currentStep = ref('')
const estimatedTime = ref(0)
const agentStatus = ref<any[]>([])
const logs = ref<any[]>([])
const logsContainer = ref()
const logBottom = ref()

// 操作状态
const isPausing = ref(false)
const isResuming = ref(false)
const isCancelling = ref(false)

// 统计数据
const totalFiles = ref(0)
const processedFiles = ref(0)
const processingTime = ref(0)
const confidenceScore = ref(0)
const elapsedSeconds = ref(0)

// WebSocket连接
let wsConnection: WebSocket | null = null
let statusPollTimer: ReturnType<typeof setInterval> | null = null
let elapsedTimer: ReturnType<typeof setInterval> | null = null

// 工作流步骤定义
const workflowSteps = ref([
  {
    id: 'file_parsing',
    title: '文件解析',
    description: '解析上传的合同和发票文件',
    status: 'idle',
    progress: 0
  },
  {
    id: 'contract_analysis',
    title: '合同分析',
    description: 'AI分析合同内容，提取关键信息',
    status: 'idle',
    progress: 0
  },
  {
    id: 'invoice_analysis',
    title: '发票分析',
    description: '批量处理发票，检测重复项',
    status: 'idle',
    progress: 0
  },
  {
    id: 'cross_validation',
    title: '交叉验证',
    description: '匹配合同与发票信息，验证一致性',
    status: 'idle',
    progress: 0
  },
  {
    id: 'report_generation',
    title: '报告生成',
    description: '生成详细的审计报告',
    status: 'idle',
    progress: 0
  }
])

// 计算属性
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'paused': 'warning',
    'cancelled': 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    'pending': '等待中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败',
    'paused': '已暂停',
    'cancelled': '已取消'
  }
  return labelMap[status] || status
}

const getProgressStatus = () => {
  if (auditStatus.value === 'failed') return 'exception'
  if (auditStatus.value === 'completed') return 'success'
  return ''
}

// WebSocket相关方法
let wsReconnectTimer: ReturnType<typeof setTimeout> | null = null
let wsReconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5

const connectWebSocket = () => {
  if (!taskId.value) return

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
  const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL
    || (apiBaseUrl.startsWith('http')
      ? apiBaseUrl.replace(/^http/, 'ws').replace(/\/api\/v1\/?$/, '')
      : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`)
  const token = encodeURIComponent(authStorage.getToken())
  const wsUrl = `${WS_BASE_URL}/ws/audit/${taskId.value}?token=${token}`
  wsConnection = new WebSocket(wsUrl)

  wsConnection.onopen = () => {
    console.log('WebSocket连接已建立')
    wsReconnectAttempts = 0
    addLog('info', '已连接到审计服务器')
  }

  wsConnection.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    } catch (error) {
      console.error('WebSocket消息解析失败:', error)
    }
  }

  wsConnection.onclose = (event) => {
    console.log('WebSocket连接已关闭, code:', event.code)
    if (auditStatus.value === 'processing' && wsReconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      addLog('warning', '连接断开，正在尝试重连...')
      wsReconnectAttempts++
      const delay = Math.min(1000 * Math.pow(2, wsReconnectAttempts), 10000)
      wsReconnectTimer = setTimeout(() => {
        addLog('info', `重连尝试 ${wsReconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`)
        connectWebSocket()
      }, delay)
    } else if (wsReconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      addLog('error', '重连次数已达上限，请刷新页面')
    }
  }

  wsConnection.onerror = (error) => {
    console.error('WebSocket错误:', error)
  }
}

const handleWebSocketMessage = (data: any) => {
  switch (data.type) {
    case 'step_change':
      handleStepChange(data.data)
      break
    case 'progress':
      updateProgress(data.data)
      break
    case 'agent_status':
      updateAgentStatus(data.data)
      break
    case 'log':
      addLog(data.data.level || 'info', data.data.message)
      break
    case 'completed':
      handleCompleted(data.data)
      break
    case 'error':
      handleError(data.data)
      break
    case 'connected':
      addLog('success', 'WebSocket连接已建立')
      break
    case 'ping':
      // 处理心跳包
      break
    default:
      console.log('未知消息类型:', data.type)
  }
}

const updateProgress = (data: any) => {
  progressPercentage.value = data.progress
  const stepName = data.current_step || data.step_name || ''
  currentStep.value = stepName
  estimatedTime.value = data.estimated_time_remaining

  // 使用 step_id 更新工作流步骤状态
  if (data.step_id) {
    const stepIndex = workflowSteps.value.findIndex(step => step.id === data.step_id)
    if (stepIndex !== -1) {
      workflowSteps.value[stepIndex].status = 'running'
      workflowSteps.value[stepIndex].progress = data.progress
    }
  }

  addLog('info', stepName ? `${stepName}: ${data.message}` : data.message)
}

const handleStepChange = (data: StepChangeData) => {
  const { previous_step_id, next_step_id, step_name, message } = data

  // 完成上一步
  if (previous_step_id) {
    const prevStep = workflowSteps.value.find(s => s.id === previous_step_id)
    if (prevStep) {
      prevStep.status = 'completed'
      prevStep.progress = 100
    }
  }

  // 启动下一步
  if (next_step_id && next_step_id !== 'completed') {
    const nextStep = workflowSteps.value.find(s => s.id === next_step_id)
    if (nextStep) {
      nextStep.status = 'running'
    }
  }

  addLog('info', message || `步骤切换: ${step_name}`)
}

const updateAgentStatus = (data: any) => {
  const existingAgent = agentStatus.value.find(agent => agent.name === data.agent_name)

  if (existingAgent) {
    Object.assign(existingAgent, data)
  } else {
    agentStatus.value.push({
      name: data.agent_name,
      status: data.status,
      start_time: new Date(),
      ...data
    })
  }

  const currentAgent = existingAgent || agentStatus.value[agentStatus.value.length - 1]
  if (data.status === 'completed' && currentAgent) {
    currentAgent.end_time = new Date()
  }

  addLog('info', `Agent ${data.agent_name}: ${data.status}`)
}

const handleCompleted = (data: any) => {
  auditStatus.value = 'completed'
  progressPercentage.value = 100

  // 标记所有步骤为完成
  workflowSteps.value.forEach(step => {
    if (step.status !== 'error') {
      step.status = 'completed'
      step.progress = 100
    }
  })

  // 标记所有Agent为完成
  agentStatus.value.forEach(agent => {
    if (agent.status !== 'error') {
      agent.status = 'completed'
      agent.end_time = new Date()
    }
  })

  addLog('success', '审计任务完成！')
  ElMessage.success('审计任务已完成')
}

const handleError = (data: any) => {
  auditStatus.value = 'failed'
  addLog('error', `审计失败: ${data.error}`)
  ElMessage.error('审计任务失败')
}

// 日志相关方法
const addLog = (level: string, message: string) => {
  logs.value.push({
    timestamp: new Date(),
    level,
    message
  })

  // 自动滚动到底部
  nextTick(() => {
    if (logBottom.value) {
      logBottom.value.scrollIntoView({ behavior: 'smooth' })
    }
  })

  // 限制日志数量
  if (logs.value.length > 100) {
    logs.value = logs.value.slice(-100)
  }
}

const clearLogs = () => {
  logs.value = []
  addLog('info', '日志已清空')
}

const downloadLogs = () => {
  const logText = logs.value.map(log =>
    `[${formatLogTime(log.timestamp)}] [${log.level.toUpperCase()}] ${log.message}`
  ).join('\n')

  const blob = new Blob([logText], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `audit_logs_${taskId.value}_${new Date().getTime()}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

// 操作方法
const pauseAudit = async () => {
  try {
    isPausing.value = true
    await apiService.post(`/audit/${taskId.value}/pause`)
    auditStatus.value = 'paused'
    addLog('warning', '审计任务已暂停')
    ElMessage.success('审计任务已暂停')
  } catch (error: any) {
    ElMessage.error('暂停失败: ' + (error.message || '未知错误'))
  } finally {
    isPausing.value = false
  }
}

const resumeAudit = async () => {
  try {
    isResuming.value = true
    await apiService.post(`/audit/${taskId.value}/resume`)
    auditStatus.value = 'processing'
    addLog('info', '审计任务已恢复')
    ElMessage.success('审计任务已恢复')
  } catch (error: any) {
    ElMessage.error('恢复失败: ' + (error.message || '未知错误'))
  } finally {
    isResuming.value = false
  }
}

const cancelAudit = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要取消当前审计任务吗？取消后无法恢复。',
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    isCancelling.value = true
    await apiService.delete(`/audit/${taskId.value}`)
    auditStatus.value = 'cancelled'
    addLog('warning', '审计任务已取消')
    ElMessage.success('审计任务已取消')

    // 延迟跳转
    setTimeout(() => {
      router.push('/audit/upload')
    }, 2000)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败: ' + (error.message || '未知错误'))
    }
  } finally {
    isCancelling.value = false
  }
}

const viewResults = () => {
  router.push(`/results/${taskId.value}`)
}

const goBack = () => {
  router.push('/audit/upload')
}

// 工具函数
const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  if (hours > 0) {
    return `${hours}小时${minutes}分${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}

const formatLogTime = (date: Date): string => {
  return date.toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const calculateDuration = (startTime: Date, endTime?: Date): string => {
  const end = endTime || new Date()
  const duration = Math.floor((end.getTime() - startTime.getTime()) / 1000)
  return formatDuration(duration)
}

// 样式类函数
const getStepClass = (status: string) => {
  return `step-${status}`
}

const getConnectorClass = (status: string) => {
  return `connector-${status}`
}

const getLogClass = (level: string) => {
  return `log-${level}`
}

const getLogIcon = (level: string) => {
  const iconMap: Record<string, any> = {
    'info': InfoFilled,
    'success': SuccessFilled,
    'warning': Warning,
    'error': Close
  }
  return iconMap[level] || InfoFilled
}

const syncStatus = async () => {
  const status = await apiService.get(`/audit/${taskId.value}/status`, undefined, { loading: false } as any)
  const prevStatus = auditStatus.value
  auditStatus.value = status.status
  progressPercentage.value = status.progress
  currentStep.value = status.current_step
  estimatedTime.value = status.estimated_time_remaining
  totalFiles.value = status.total_files || 0
  processedFiles.value = status.processed_files || 0
  processingTime.value = status.processing_time || 0
  confidenceScore.value = status.confidence_score || 0

  // 首次获取状态时，如果审计已在进行中，生成上下文日志
  if (prevStatus === 'pending' && status.status === 'processing' && status.progress > 0) {
    addLog('info', `审计已在进行中 - 当前进度: ${status.progress}%`)
    addLog('info', `当前步骤: ${status.current_step || '处理中'}`)
    if (status.processing_time > 0) {
      addLog('info', `已处理: ${Math.round(status.processing_time)}秒`)
    }
  }

  if (status.status === 'completed') {
    handleCompleted({ task_id: taskId.value })
    if (statusPollTimer) {
      clearInterval(statusPollTimer)
      statusPollTimer = null
    }
  } else if (status.status === 'failed') {
    handleError({ error: status.error_message || '审计任务失败' })
    if (statusPollTimer) {
      clearInterval(statusPollTimer)
      statusPollTimer = null
    }
  }
}

// 生命周期
onMounted(async () => {
  if (taskId.value) {
    // 连接WebSocket
    connectWebSocket()

    // 耗时计时器（每秒更新）
    elapsedTimer = setInterval(() => {
      if (auditStatus.value === 'processing') {
        elapsedSeconds.value++
      }
    }, 1000)

    // 获取初始状态
    try {
      await syncStatus()
      statusPollTimer = setInterval(() => {
        syncStatus().catch(error => {
          console.error('轮询状态失败:', error)
        })
      }, 3000)

      // 添加初始日志
      addLog('info', '审计页面已加载')
      addLog('info', `任务ID: ${taskId.value}`)
    } catch (error) {
      console.error('获取状态失败:', error)
      addLog('error', '无法获取审计状态')
    }
  }
})

onUnmounted(() => {
  if (wsReconnectTimer) {
    clearTimeout(wsReconnectTimer)
    wsReconnectTimer = null
  }
  if (statusPollTimer) {
    clearInterval(statusPollTimer)
    statusPollTimer = null
  }
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
    elapsedTimer = null
  }
  if (wsConnection) {
    wsConnection.onclose = null  // 防止重连
    wsConnection.close()
    wsConnection = null
  }
})
</script>

<style scoped>
.processing-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  margin-top: 16px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.page-description {
  font-size: 16px;
  color: #606266;
  margin: 0;
}

.main-content {
  margin-top: 24px;
}

.status-card {
  margin-bottom: 24px;
}

.status-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 32px;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.status-value {
  font-size: 14px;
  color: #303133;
  font-weight: 600;
}

.progress-section {
  flex: 1;
  max-width: 400px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.progress-value {
  font-size: 16px;
  color: #303133;
  font-weight: 600;
}

.main-progress {
  margin-bottom: 8px;
}

.workflow-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 18px;
  color: #409EFF;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.workflow-content {
  margin-top: 16px;
}

.steps-container {
  position: relative;
  padding: 24px 0;
}

.step-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 32px;
  position: relative;
}

.step-item:last-child {
  margin-bottom: 0;
}

.step-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #F5F7FA;
  border: 2px solid #E4E7ED;
  color: #909399;
  font-size: 20px;
  flex-shrink: 0;
  margin-right: 16px;
  z-index: 2;
}

.step-item.step-completed .step-icon {
  background-color: #F0F9FF;
  border-color: #409EFF;
  color: #409EFF;
}

.step-item.step-running .step-icon {
  background-color: #FDF6EC;
  border-color: #E6A23C;
  color: #E6A23C;
}

.step-item.step-error .step-icon {
  background-color: #FEF0F0;
  border-color: #F56C6C;
  color: #F56C6C;
}

.step-content {
  flex: 1;
  padding-top: 8px;
}

.step-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.step-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.step-progress {
  width: 200px;
}

.step-connector {
  position: absolute;
  left: 23px;
  top: 48px;
  width: 2px;
  height: 32px;
  background-color: #E4E7ED;
  z-index: 1;
}

.step-item.step-completed .step-connector {
  background-color: #409EFF;
}

.step-item.step-running .step-connector {
  background-color: #E6A23C;
}

.step-item.step-error .step-connector {
  background-color: #F56C6C;
}

.logs-card {
  margin-bottom: 24px;
  height: 500px;
}

.logs-content {
  height: calc(100% - 60px);
  overflow-y: auto;
  background-color: #1F2937;
  border-radius: 6px;
  padding: 16px;
}

.log-entries {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.log-entry {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 12px;
  line-height: 1.4;
}

.log-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  gap: 16px;
}

.log-waiting-icon {
  font-size: 32px;
}

.log-waiting-text {
  color: #9CA3AF;
  font-size: 14px;
}

.log-time {
  color: #9CA3AF;
  min-width: 80px;
}

.log-icon {
  font-size: 14px;
}

.log-entry.log-info .log-icon {
  color: #60A5FA;
}

.log-entry.log-success .log-icon {
  color: #34D399;
}

.log-entry.log-warning .log-icon {
  color: #FBBF24;
}

.log-entry.log-error .log-icon {
  color: #F87171;
}

.log-message {
  flex: 1;
  word-break: break-all;
}

.log-entry.log-info .log-message {
  color: #E5E7EB;
}

.log-entry.log-success .log-message {
  color: #34D399;
}

.log-entry.log-warning .log-message {
  color: #FBBF24;
}

.log-entry.log-error .log-message {
  color: #F87171;
}

.log-bottom {
  height: 1px;
}

.action-card {
  margin-bottom: 24px;
}

.action-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 32px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.stats-section {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.stat-label {
  color: #606266;
}

.stat-value {
  color: #303133;
  font-weight: 600;
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .processing-page {
    padding: 16px;
  }

  .page-title {
    font-size: 24px;
  }

  .status-content {
    flex-direction: column;
    gap: 16px;
  }

  .progress-section {
    max-width: 100%;
  }

  .action-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .stats-section {
    flex-direction: column;
    gap: 8px;
  }

  .success-summary {
    grid-template-columns: 1fr;
  }
}
</style>
