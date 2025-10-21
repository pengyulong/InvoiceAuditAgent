<template>
  <div class="processing-container">
    <div class="processing-header">
      <el-button type="text" @click="goBack" class="back-button">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2>审计处理中</h2>
    </div>

    <div class="processing-content">
      <!-- 任务状态卡片 -->
      <el-card class="status-card">
        <template #header>
          <div class="card-header">
            <el-icon><DataAnalysis /></el-icon>
            <span>任务状态</span>
          </div>
        </template>

        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="4" animated />
        </div>

        <div v-else-if="task" class="task-status">
          <div class="task-info">
            <h3>{{ task.task_name }}</h3>
            <div class="task-meta">
              <el-tag :type="getStatusType(task.status)" size="large">
                {{ getStatusText(task.status) }}
              </el-tag>
              <span class="task-id">任务ID: {{ task.id }}</span>
            </div>
          </div>

          <div class="progress-section">
            <div class="progress-header">
              <span>处理进度</span>
              <span class="progress-percentage">{{ Math.round(task.progress_percentage || 0) }}%</span>
            </div>
            <el-progress
              :percentage="Math.round(task.progress_percentage || 0)"
              :status="getProgressStatus(task.status)"
              :stroke-width="10"
              :striped="task.status === 'processing'"
              :animated="task.status === 'processing'"
            >
              <template #default="{ percentage }">
                <span class="progress-text">{{ Math.round(percentage) }}%</span>
              </template>
            </el-progress>
            <div class="current-step">
              <el-icon :class="getStepIcon(task.status)">
                <component :is="getStepIcon(task.status)" />
              </el-icon>
              <span>{{ task.current_step || '准备中...' }}</span>
              <div v-if="task.status === 'processing'" class="processing-indicator">
                <span class="processing-dot"></span>
                <span class="processing-dot"></span>
                <span class="processing-dot"></span>
              </div>
            </div>
          </div>

          <div class="task-stats">
            <div class="stat-item">
              <span class="stat-label">文件总数</span>
              <span class="stat-value">{{ task.total_files }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">已处理</span>
              <span class="stat-value">{{ task.processed_files }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">开始时间</span>
              <span class="stat-value">{{ formatTime(task.created_at) }}</span>
            </div>
            <div v-if="task.completed_at" class="stat-item">
              <span class="stat-label">完成时间</span>
              <span class="stat-value">{{ formatTime(task.completed_at) }}</span>
            </div>
          </div>
        </div>

        <div v-else class="error-state">
          <el-result
            icon="error"
            title="任务不存在"
            sub-title="请检查任务ID是否正确"
          >
            <template #extra>
              <el-button type="primary" @click="goBack">返回</el-button>
            </template>
          </el-result>
        </div>
      </el-card>

      <!-- 实时日志 -->
      <el-card class="logs-card">
        <template #header>
          <div class="card-header">
            <el-icon><Document /></el-icon>
            <span>处理日志</span>
            <el-button type="text" @click="toggleAutoScroll">
              <el-icon><Sort /></el-icon>
              {{ autoScroll ? '停止滚动' : '自动滚动' }}
            </el-button>
          </div>
        </template>

        <div ref="logContainer" class="log-container" :class="{ 'auto-scroll': autoScroll }">
          <div v-if="logs.length === 0" class="empty-logs">
            <el-empty description="暂无日志" />
          </div>
          <div v-else class="log-list">
            <div
              v-for="(log, index) in logs"
              :key="index"
              class="log-item"
              :class="getLogLevelClass(log.level)"
            >
              <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
              <span class="log-level">{{ log.level.toUpperCase() }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <div class="primary-actions">
          <el-button
            v-if="task?.status === 'pending'"
            type="primary"
            size="large"
            @click="startTask"
          >
            <el-icon><VideoPlay /></el-icon>
            开始审计
          </el-button>
          <el-button
            v-if="task?.status === 'completed'"
            type="success"
            size="large"
            @click="viewResults"
          >
            <el-icon><View /></el-icon>
            查看结果
          </el-button>
        </div>

        <div class="secondary-actions">
          <el-button
            v-if="task?.status === 'failed'"
            type="danger"
            @click="retryTask"
          >
            <el-icon><RefreshRight /></el-icon>
            重试
          </el-button>
          <el-button @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuditStore } from '@/stores/audit'
import type { AuditTask } from '@/types/audit'

const route = useRoute()
const router = useRouter()
const auditStore = useAuditStore()

const taskId = route.params.taskId as string
const loading = ref(true)
const task = ref<AuditTask | null>(null)
const auditId = ref<string>('')
const logs = ref<Array<{ timestamp: string; level: string; message: string }>>([])
const autoScroll = ref(true)
const logContainer = ref<HTMLElement>()
let websocket: WebSocket | null = null
let refreshTimer: NodeJS.Timeout | null = null

// WebSocket连接
const connectWebSocket = () => {
  try {
    // 修复：始终使用task_id连接WebSocket，因为后端使用task_id作为连接键
    const wsUrl = `ws://localhost:8000/ws/audit/${taskId}`
    websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      console.log('WebSocket连接成功')
      addLog({
        timestamp: new Date().toISOString(),
        level: 'info',
        message: 'WebSocket连接已建立，正在监听审计进度...'
      })
    }

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('收到WebSocket消息:', data)

        if (data.type === 'connection_established') {
          addLog({
            timestamp: new Date().toISOString(),
            level: 'info',
            message: '已建立实时连接，准备接收审计进度更新'
          })
        } else if (data.type === 'progress') {
          // 更新任务状态
          updateTaskStatus(data.data)
          // 添加进度日志
          addLog({
            timestamp: new Date().toISOString(),
            level: 'info',
            message: `[${data.data.step}] ${data.data.message} (${data.data.progress}%)`
          })
        } else if (data.type === 'agent_update') {
          // Agent状态更新
          addLog({
            timestamp: new Date().toISOString(),
            level: 'info',
            message: `[${data.data.agent_name}] ${data.data.status}`
          })
        } else if (data.type === 'file_processed') {
          // 文件处理完成
          addLog({
            timestamp: new Date().toISOString(),
            level: 'success',
            message: `文件处理完成: ${data.data.file_info.file_name}`
          })
        } else if (data.type === 'audit_completed') {
          // 任务完成
          addLog({
            timestamp: new Date().toISOString(),
            level: 'success',
            message: '🎉 审计任务已完成！'
          })
          if (task.value) {
            task.value.status = 'completed'
            task.value.progress_percentage = 100
            task.value.current_step = '审计完成'
          }
          if (refreshTimer) {
            clearInterval(refreshTimer)
          }
        } else if (data.type === 'error') {
          // 错误信息
          addLog({
            timestamp: new Date().toISOString(),
            level: 'error',
            message: `❌ 错误: ${data.data.error_message}`
          })
        } else if (data.type === 'ping') {
          // 心跳消息，忽略
          return
        }
      } catch (parseError) {
        console.error('解析WebSocket消息失败:', parseError)
        addLog({
          timestamp: new Date().toISOString(),
          level: 'error',
          message: `消息解析错误: ${parseError.message}`
        })
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket错误:', error)
    }

    websocket.onclose = () => {
      console.log('WebSocket连接关闭')
      // 尝试重连
      setTimeout(() => {
        if (route.name === 'AuditProcessing') {
          connectWebSocket()
        }
      }, 5000)
    }
  } catch (error) {
    console.error('WebSocket连接失败:', error)
  }
}

// 更新任务状态
const updateTaskStatus = (payload: any) => {
  if (task.value) {
    // 添加进度变化的详细日志
    const oldProgress = task.value.progress_percentage || 0
    const newProgress = payload.progress || 0
    const step = payload.step || payload.current_step || '处理中'
    const message = payload.message || '正在处理...'

    // 如果进度有显著变化，添加详细日志
    if (newProgress > oldProgress) {
      console.log(`进度更新: ${oldProgress}% → ${newProgress}%, 步骤: ${step}`)
    }

    task.value.progress_percentage = newProgress
    task.value.current_step = step
    if (payload.processed_files !== undefined) {
      task.value.processed_files = payload.processed_files
    }

    // 根据进度推断任务状态
    if (newProgress > 0 && newProgress < 100) {
      task.value.status = 'processing'
    } else if (newProgress >= 100) {
      task.value.status = 'completed'
    }
  }
}

// 添加日志
const addLog = (logEntry: any) => {
  // 确保日志格式正确
  const formattedLog = {
    timestamp: logEntry.timestamp || new Date().toISOString(),
    level: logEntry.level || 'info',
    message: logEntry.message || ''
  }

  // 添加日志到列表
  logs.value.push(formattedLog)

  // 限制日志数量，保留最新的200条
  if (logs.value.length > 200) {
    logs.value = logs.value.slice(-200)
  }

  // 自动滚动到底部
  if (autoScroll.value) {
    nextTick(() => {
      scrollToBottom()
    })
  }

  // 控制台输出重要日志
  if (formattedLog.level === 'error') {
    console.error(`[${formattedLog.level.toUpperCase()}] ${formattedLog.message}`)
  } else if (formattedLog.level === 'warning') {
    console.warn(`[${formattedLog.level.toUpperCase()}] ${formattedLog.message}`)
  } else {
    console.log(`[${formattedLog.level.toUpperCase()}] ${formattedLog.message}`)
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

// 切换自动滚动
const toggleAutoScroll = () => {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) {
    scrollToBottom()
  }
}

// 加载任务数据
const loadTask = async () => {
  try {
    task.value = await auditStore.getTask(taskId)
    if (!task.value) {
      loading.value = false
      return
    }

    // 如果任务有audit ID，更新本地状态
    if (task.value.audit_id) {
      auditId.value = task.value.audit_id
    }

    // 如果任务已完成或失败，添加一些示例日志
    if (task.value.status === 'completed' || task.value.status === 'failed') {
      logs.value = [
        {
          timestamp: task.value.created_at,
          level: 'info',
          message: '任务开始执行'
        },
        {
          timestamp: task.value.created_at,
          level: 'info',
          message: '正在解析ZIP文件...'
        },
        {
          timestamp: task.value.created_at,
          level: 'info',
          message: '识别到合同和发票文件'
        },
        {
          timestamp: task.value.created_at,
          level: 'info',
          message: '开始AI分析...'
        }
      ]
    }
  } catch (error) {
    console.error('加载任务失败:', error)
  } finally {
    loading.value = false
  }
}

// 页面导航
const goBack = () => {
  router.push('/audit')
}

const viewResults = () => {
  router.push(`/results/${taskId}`)
}

const startTask = async () => {
  try {
    // 清空现有日志
    logs.value = []

    // 添加启动前日志
    addLog({
      timestamp: new Date().toISOString(),
      level: 'info',
      message: '🚀 准备启动审计任务...'
    })

    addLog({
      timestamp: new Date().toISOString(),
      level: 'info',
      message: `任务ID: ${taskId}`
    })

    // 启动任务
    const auditResult = await auditStore.startAudit(taskId)
    if (auditResult) {
      // 添加成功启动日志
      addLog({
        timestamp: new Date().toISOString(),
        level: 'success',
        message: '✅ 审计任务启动成功'
      })

      addLog({
        timestamp: new Date().toISOString(),
        level: 'info',
        message: '📋 正在初始化审计流程...'
      })

      addLog({
        timestamp: new Date().toISOString(),
        level: 'info',
        message: '🔍 正在建立实时连接...'
      })

      // 更新audit ID
      if (typeof auditResult === 'string') {
        auditId.value = auditResult
        addLog({
          timestamp: new Date().toISOString(),
          level: 'info',
          message: `审计ID: ${auditResult}`
        })
      } else if (task.value?.audit_id) {
        auditId.value = task.value.audit_id
        addLog({
          timestamp: new Date().toISOString(),
          level: 'info',
          message: `审计ID: ${task.value.audit_id}`
        })
      }

      // 更新任务状态
      if (task.value) {
        task.value.status = 'processing'
        task.value.current_step = '开始审计'
        task.value.progress_percentage = 1
      }

      // 连接WebSocket
      connectWebSocket()

      // 定期刷新任务状态
      refreshTimer = setInterval(async () => {
        await loadTask()
      }, 3000) // 减少到3秒刷新一次，提高实时性

      addLog({
        timestamp: new Date().toISOString(),
        level: 'info',
        message: '⏱️ 已启动状态监控，每3秒刷新一次'
      })
    }
  } catch (error) {
    console.error('启动任务失败:', error)
    // 添加详细错误日志
    addLog({
      timestamp: new Date().toISOString(),
      level: 'error',
      message: `❌ 启动审计失败: ${error.message || error}`
    })

    addLog({
      timestamp: new Date().toISOString(),
      level: 'warning',
      message: '💡 请检查网络连接或稍后重试'
    })

    // 更新任务状态为失败
    if (task.value) {
      task.value.status = 'failed'
      task.value.current_step = '启动失败'
    }
  }
}

const retryTask = async () => {
  try {
    // 重新开始任务
    const auditResult = await auditStore.startAudit(taskId)
    if (auditResult) {
      // 清空日志
      logs.value = []
      // 更新audit ID
      if (typeof auditResult === 'string') {
        auditId.value = auditResult
      } else if (task.value?.audit_id) {
        auditId.value = task.value.audit_id
      }
      // 重新连接WebSocket
      connectWebSocket()
    }
  } catch (error) {
    console.error('重试任务失败:', error)
  }
}

// 工具方法
const getStatusType = (status: string) => {
  const statusMap = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap = {
    'pending': '等待中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || '未知'
}

const getProgressStatus = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return ''
}

const getLogLevelClass = (level: string) => {
  return `log-${level.toLowerCase()}`
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString()
}

const formatLogTime = (time: string) => {
  const date = new Date(time)
  return date.toLocaleTimeString()
}

// 获取步骤图标
const getStepIcon = (status: string) => {
  const iconMap = {
    'pending': 'Clock',
    'processing': 'Loading',
    'completed': 'CircleCheck',
    'failed': 'CircleClose'
  }
  return iconMap[status] || 'Clock'
}

// 监听任务状态变化
watch(
  () => task.value?.status,
  (newStatus) => {
    if (newStatus === 'completed' || newStatus === 'failed') {
      if (refreshTimer) {
        clearInterval(refreshTimer)
      }
    }
  }
)

// 生命周期
onMounted(async () => {
  await loadTask()

  if (task.value && task.value.status === 'processing') {
    connectWebSocket()

    // 定期刷新任务状态
    refreshTimer = setInterval(async () => {
      await loadTask()
    }, 5000)
  }
})

onUnmounted(() => {
  if (websocket) {
    websocket.close()
    websocket = null
  }
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.processing-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

.processing-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.back-button {
  font-size: 1rem;
}

.processing-header h2 {
  font-size: 1.8rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.status-card {
  margin-bottom: 2rem;
}

.loading-container {
  padding: 2rem;
}

.task-status {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.task-info h3 {
  font-size: 1.3rem;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.task-id {
  color: #6b7280;
  font-size: 0.9rem;
}

.progress-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.progress-percentage {
  color: #3b82f6;
  font-weight: 600;
}

.current-step {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6b7280;
  font-size: 0.9rem;
}

.task-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
}

.stat-label {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-weight: 600;
  color: #1f2937;
}

.logs-card {
  margin-bottom: 2rem;
}

.log-container {
  height: 300px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
  background: #f8fafc;
}

.log-container.auto-scroll {
  scroll-behavior: smooth;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.log-item {
  display: flex;
  gap: 1rem;
  padding: 0.5rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.log-item.log-info {
  background: rgba(59, 130, 246, 0.1);
  border-left: 3px solid #3b82f6;
}

.log-item.log-warning {
  background: rgba(245, 158, 11, 0.1);
  border-left: 3px solid #f59e0b;
}

.log-item.log-error {
  background: rgba(239, 68, 68, 0.1);
  border-left: 3px solid #ef4444;
}

.log-item.log-success {
  background: rgba(34, 197, 94, 0.1);
  border-left: 3px solid #22c55e;
}

.log-time {
  color: #6b7280;
  min-width: 80px;
}

.log-level {
  color: #1f2937;
  font-weight: 600;
  min-width: 50px;
}

.log-message {
  flex: 1;
  color: #374151;
}

.empty-logs {
  text-align: center;
  padding: 2rem;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  align-items: center;
}

.primary-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.primary-actions .el-button {
  min-width: 140px;
  font-weight: 600;
}

.secondary-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.secondary-actions .el-button {
  min-width: 100px;
}

.error-state {
  text-align: center;
  padding: 2rem;
}

@media (max-width: 768px) {
  .processing-container {
    padding: 1rem;
  }

  .processing-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .task-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .progress-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .task-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .log-item {
    flex-direction: column;
    gap: 0.25rem;
  }

  .action-buttons {
    flex-direction: column;
  }
}

/* 动态进度条动画效果 */
/* 进度条动画效果 */
.progress-bar-animated {
  position: relative;
  overflow: hidden;
}

.progress-bar-animated::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: progress-shimmer 2s infinite;
}

@keyframes progress-shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

/* 处理中阶段的步骤图标动画 */
.step-icon.processing {
  animation: step-processing 1.5s ease-in-out infinite;
}

@keyframes step-processing {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

/* 处理日志的进入动画 */
.log-item {
  animation: log-slide-in 0.3s ease-out;
}

@keyframes log-slide-in {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 当前处理阶段的高亮效果 */
.current-step {
  position: relative;
}

.current-step::before {
  content: '';
  position: absolute;
  left: -8px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 20px;
  background: #409eff;
  border-radius: 2px;
  animation: step-highlight 2s ease-in-out infinite;
}

@keyframes step-highlight {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* 处理指示器动画 */
.processing-indicator {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.processing-dot {
  width: 6px;
  height: 6px;
  background: #409eff;
  border-radius: 50%;
  animation: processing-pulse 1.4s ease-in-out infinite both;
}

.processing-dot:nth-child(1) { animation-delay: -0.32s; }
.processing-dot:nth-child(2) { animation-delay: -0.16s; }
.processing-dot:nth-child(3) { animation-delay: 0s; }

@keyframes processing-pulse {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 重新开始按钮的动画 */
.restart-hint {
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-5px); }
  60% { transform: translateY(-3px); }
}

/* 空状态图标的动画 */
.empty-state-icon {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}
</style>