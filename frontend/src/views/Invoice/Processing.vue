<template>
  <div class="processing-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: '/invoice/upload' }">发票识别</el-breadcrumb-item>
        <el-breadcrumb-item>识别进度</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="header-content">
        <h1 class="page-title">发票识别进度</h1>
        <p class="page-description">实时监控OCR识别处理过程</p>
      </div>
    </div>

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
              <el-tag :type="statusType" size="large">{{ statusLabel }}</el-tag>
            </div>
            <div class="status-item" v-if="isRunning">
              <span class="status-label">已耗时:</span>
              <span class="status-value">{{ formatDuration(elapsedSeconds) }}</span>
            </div>
          </div>

          <div class="progress-section">
            <div class="progress-header">
              <span class="progress-label">整体进度</span>
              <span class="progress-value">{{ progress }}%</span>
            </div>
            <el-progress
              :percentage="progress"
              :stroke-width="12"
              :status="progressStatus"
              class="main-progress"
            />
          </div>
        </div>
      </el-card>

      <el-alert
        v-if="errorMessage"
        class="error-alert"
        type="error"
        :title="errorMessage"
        show-icon
        :closable="false"
      />

      <!-- 工作流步骤 -->
      <el-card class="workflow-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="header-icon">⚙️</span>
            <span class="header-title">处理流程</span>
          </div>
        </template>

        <div class="workflow-content">
          <div class="workflow-steps">
            <div
              v-for="(step, index) in steps"
              :key="step.id"
              class="step-item"
              :class="`step-${step.status}`"
            >
              <div class="step-icon">
                <span v-if="step.status === 'completed'">✅</span>
                <span v-else-if="step.status === 'running'" class="rotating">⏳</span>
                <span v-else-if="step.status === 'error'">❌</span>
                <span v-else>🕐</span>
              </div>
              <div class="step-content">
                <h4>{{ step.name }}</h4>
                <p>{{ step.description }}</p>
              </div>
              <div class="step-connector" v-if="index < steps.length - 1" />
            </div>
          </div>
        </div>
      </el-card>

      <!-- 日志区域 -->
      <el-card class="log-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="header-icon">📝</span>
            <span class="header-title">识别日志</span>
            <span class="log-count">{{ logs.length }} 条</span>
          </div>
        </template>

        <div class="log-content" ref="logContainer">
          <div v-if="logs.length === 0" class="log-empty">
            <p>等待识别输出...</p>
          </div>
          <div
            v-for="(log, index) in logs"
            :key="index"
            class="log-item"
            :class="`log-${log.level}`"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiService, authStorage } from '@/services/api'

const router = useRouter()
const route = useRoute()

const taskId = ref(route.params.taskId as string)

const status = ref('pending')
const progress = ref(0)
const elapsedSeconds = ref(0)
const errorMessage = ref('')
let elapsedTimer: any = null
let ws: WebSocket | null = null

const logs = ref<Array<{ time: string; level: string; message: string }>>([])
const logContainer = ref<HTMLElement>()

const isRunning = computed(() => status.value === 'running' || status.value === 'processing')
const statusType = computed(() => {
  const map: Record<string, string> = {
    pending: 'info', running: 'warning', processing: 'warning',
    completed: 'success', failed: 'danger',
  }
  return map[status.value] || 'info'
})
const statusLabel = computed(() => {
  const map: Record<string, string> = {
    pending: '等待中', running: '识别中', processing: '识别中',
    completed: '已完成', failed: '失败',
  }
  return map[status.value] || status.value
})
const progressStatus = computed(() => {
  if (status.value === 'failed') return 'exception'
  if (status.value === 'completed') return 'success'
  return undefined
})

const steps = ref([
  { id: 'upload', name: '文件上传', description: '上传发票文件到服务器', status: 'completed' },
  { id: 'ocr', name: 'OCR识别', description: 'AI识别发票关键信息', status: 'pending' },
  { id: 'done', name: '识别完成', description: '汇总结果，生成报告', status: 'pending' },
])

const updateStep = (stepId: string, stepStatus: string) => {
  const step = steps.value.find(s => s.id === stepId)
  if (step) step.status = stepStatus
}

const addLog = (level: string, message: string) => {
  const now = new Date()
  const time = now.toLocaleTimeString('zh-CN', { hour12: false })
  logs.value.push({ time, level, message })
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

const connectWebSocket = () => {
  if (!taskId.value) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host || 'localhost:8080'
  const token = authStorage.getToken()
  const url = `${protocol}//${host}/ws/audit/${taskId.value}?token=${encodeURIComponent(token)}`

  ws = new WebSocket(url)

  ws.onopen = () => {
    addLog('info', 'WebSocket已连接，等待识别开始...')
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'progress') {
        progress.value = data.data?.progress || data.progress || 0
        updateStep('ocr', 'running')
      } else if (data.type === 'log') {
        addLog(data.level || 'info', data.message || data.data?.message || '')
      } else if (data.type === 'completed') {
        status.value = 'completed'
        progress.value = 100
        updateStep('ocr', 'completed')
        updateStep('done', 'completed')
        addLog('success', '识别完成！即将跳转到结果页面...')
        if (elapsedTimer) clearInterval(elapsedTimer)
        setTimeout(() => {
          router.push(`/invoice/results/${taskId.value}`)
        }, 1500)
      } else if (data.type === 'error') {
        status.value = 'failed'
        updateStep('ocr', 'error')
        const message = data.data?.error || data.data?.message || data.message || '识别失败'
        errorMessage.value = message
        addLog('error', message)
        ElMessage.error(message)
        if (elapsedTimer) clearInterval(elapsedTimer)
      }
    } catch {
      // 非JSON消息，忽略
    }
  }

  ws.onclose = () => {
    addLog('warning', 'WebSocket连接已关闭')
  }

  ws.onerror = () => {
    addLog('error', 'WebSocket连接出错')
  }
}

const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins > 0) return `${mins}分${secs}秒`
  return `${secs}秒`
}

onMounted(() => {
  if (!taskId.value) {
    ElMessage.error('缺少任务ID')
    router.push('/invoice/upload')
    return
  }

  status.value = 'running'
  elapsedTimer = setInterval(() => {
    if (isRunning.value) elapsedSeconds.value++
  }, 1000)

  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
    elapsedTimer = null
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
  max-width: 1280px;
  margin-left: auto;
  margin-right: auto;
}

.status-card {
  margin-bottom: 24px;
}

.error-alert {
  margin-bottom: 24px;
}

.status-content {
  padding: 8px;
}

.status-info {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-size: 14px;
  color: #909399;
}

.status-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.progress-section {
  margin-top: 8px;
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
}

.progress-value {
  font-size: 18px;
  font-weight: 600;
  color: #409EFF;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 18px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.log-count {
  margin-left: auto;
  font-size: 13px;
  color: #909399;
}

.workflow-card {
  margin-bottom: 24px;
}

.workflow-steps {
  display: flex;
  flex-direction: column;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 0;
  position: relative;
}

.step-icon {
  font-size: 24px;
  width: 40px;
  text-align: center;
  flex-shrink: 0;
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.step-content h4 {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.step-content p {
  font-size: 13px;
  color: #909399;
  margin: 0;
}

.step-completed .step-content h4 {
  color: #67C23A;
}

.step-running .step-content h4 {
  color: #409EFF;
}

.step-error .step-content h4 {
  color: #F56C6C;
}

.log-card {
  margin-bottom: 24px;
}

.log-content {
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.log-empty {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.log-item {
  padding: 6px 0;
  border-bottom: 1px solid #F5F5F5;
  display: flex;
  gap: 12px;
}

.log-time {
  color: #909399;
  white-space: nowrap;
  flex-shrink: 0;
}

.log-message {
  color: #303133;
}

.log-success .log-message {
  color: #67C23A;
}

.log-error .log-message {
  color: #F56C6C;
}

.log-warning .log-message {
  color: #E6A23C;
}

@media (max-width: 768px) {
  .processing-page {
    padding: 16px;
  }

  .page-title {
    font-size: 24px;
  }

  .status-info {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
