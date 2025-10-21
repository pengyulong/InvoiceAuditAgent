<template>
  <div class="audit-container">
    <div class="audit-header">
      <h1>审计工作台</h1>
      <p>智能合同发票审计系统</p>
    </div>

    <div class="audit-content">
      <!-- 快速操作卡片 -->
      <div class="quick-actions">
        <el-card class="action-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Upload /></el-icon>
              <span>快速开始</span>
            </div>
          </template>
          <div class="action-content">
            <el-button type="primary" size="large" @click="goToUpload">
              <el-icon><DocumentAdd /></el-icon>
              上传审计文件
            </el-button>
            <p class="action-tip">上传包含合同和发票的ZIP文件开始审计</p>
          </div>
        </el-card>

        <el-card class="action-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><List /></el-icon>
              <span>任务管理</span>
            </div>
          </template>
          <div class="action-content">
            <el-button size="large" @click="goToTasks">
              <el-icon><FolderOpened /></el-icon>
              查看所有任务
            </el-button>
            <p class="action-tip">管理和监控所有审计任务</p>
          </div>
        </el-card>

        <el-card class="action-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>统计报告</span>
            </div>
          </template>
          <div class="action-content">
            <el-button size="large" @click="goToResults">
              <el-icon><PieChart /></el-icon>
              查看统计数据
            </el-button>
            <p class="action-tip">查看审计统计和分析报告</p>
          </div>
        </el-card>
      </div>

      <!-- 最近任务 -->
      <div class="recent-tasks">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>最近任务</span>
              <el-button type="text" @click="refreshTasks">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>

          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="3" animated />
          </div>

          <div v-else-if="recentTasks.length === 0" class="empty-state">
            <el-empty description="暂无任务">
              <el-button type="primary" @click="goToUpload">开始第一个审计</el-button>
            </el-empty>
          </div>

          <div v-else class="task-list">
            <div
              v-for="task in recentTasks"
              :key="task.id"
              class="task-item"
              @click="viewTask(task.id)"
            >
              <div class="task-info">
                <div class="task-name">{{ task.task_name }}</div>
                <div class="task-meta">
                  <el-tag :type="getStatusType(task.status)" size="small">
                    {{ getStatusText(task.status) }}
                  </el-tag>
                  <span class="task-time">{{ formatTime(task.created_at) }}</span>
                </div>
              </div>
              <div class="task-progress">
                <el-progress
                  :percentage="task.progress_percentage || 0"
                  :status="getProgressStatus(task.status)"
                  :stroke-width="6"
                />
                <span class="progress-text">{{ task.current_step }}</span>
              </div>
            </div>
          </div>

          <div v-if="recentTasks.length > 0" class="view-all">
            <el-button type="text" @click="goToTasks">
              查看全部任务
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuditStore } from '@/stores/audit'
import type { AuditTask } from '@/types/audit'

const router = useRouter()
const auditStore = useAuditStore()

const loading = ref(false)
const recentTasks = ref<AuditTask[]>([])

// 页面导航方法
const goToUpload = () => {
  router.push('/audit/upload')
}

const goToTasks = () => {
  router.push('/audit/tasks')
}

const goToResults = () => {
  router.push('/results')
}

const viewTask = (taskId: string) => {
  if (recentTasks.value.find(task => task.id === taskId)?.status === 'processing') {
    router.push(`/audit/processing/${taskId}`)
  } else {
    router.push(`/audit/processing/${taskId}`)
  }
}

// 数据加载方法
const loadRecentTasks = async () => {
  loading.value = true
  try {
    recentTasks.value = await auditStore.getRecentTasks(5)
  } catch (error) {
    console.error('加载最近任务失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshTasks = () => {
  loadRecentTasks()
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

const formatTime = (time: string) => {
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}

// 生命周期
onMounted(() => {
  loadRecentTasks()
})
</script>

<style scoped>
.audit-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.audit-header {
  text-align: center;
  margin-bottom: 3rem;
}

.audit-header h1 {
  font-size: 2.5rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.audit-header p {
  color: #6b7280;
  font-size: 1.1rem;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.action-content {
  text-align: center;
}

.action-tip {
  margin-top: 1rem;
  color: #6b7280;
  font-size: 0.9rem;
}

.recent-tasks {
  margin-top: 2rem;
}

.loading-container {
  padding: 1rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.task-item:hover {
  border-color: #3b82f6;
  background-color: #f8fafc;
}

.task-info {
  flex: 1;
}

.task-name {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.task-time {
  color: #6b7280;
  font-size: 0.8rem;
}

.task-progress {
  flex: 1;
  max-width: 300px;
  margin-left: 2rem;
}

.progress-text {
  display: block;
  text-align: center;
  color: #6b7280;
  font-size: 0.8rem;
  margin-top: 0.5rem;
}

.view-all {
  text-align: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

@media (max-width: 768px) {
  .audit-container {
    padding: 1rem;
  }

  .audit-header h1 {
    font-size: 2rem;
  }

  .quick-actions {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .task-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .task-progress {
    margin-left: 0;
    margin-top: 1rem;
    max-width: 100%;
  }
}
</style>