<template>
  <div class="results-container">
    <div class="results-header">
      <el-button type="text" @click="goBack" class="back-button">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2>审计结果</h2>
    </div>

    <div class="results-content">
      <!-- 统计概览 -->
      <el-card class="overview-card">
        <template #header>
          <div class="card-header">
            <el-icon><DataAnalysis /></el-icon>
            <span>统计概览</span>
            <el-button type="text" @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>

        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="3" animated />
        </div>

        <div v-else class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.total_tasks }}</div>
              <div class="stat-label">总任务数</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon success">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.completed_tasks }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon processing">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.processing_tasks }}</div>
              <div class="stat-label">处理中</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon failed">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.failed_tasks }}</div>
              <div class="stat-label">失败</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon contracts">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.total_contracts }}</div>
              <div class="stat-label">合同总数</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon invoices">
              <el-icon><Receipt /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.total_invoices }}</div>
              <div class="stat-label">发票总数</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon rate">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.success_rate.toFixed(1) }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 任务列表 -->
      <el-card class="tasks-card">
        <template #header>
          <div class="card-header">
            <el-icon><List /></el-icon>
            <span>任务列表</span>
            <div class="header-actions">
              <el-select
                v-model="statusFilter"
                placeholder="筛选状态"
                clearable
                @change="loadTasks"
              >
                <el-option label="全部" value="" />
                <el-option label="等待中" value="pending" />
                <el-option label="处理中" value="processing" />
                <el-option label="已完成" value="completed" />
                <el-option label="失败" value="failed" />
              </el-select>
            </div>
          </div>
        </template>

        <div v-if="tasksLoading" class="loading-container">
          <el-skeleton :rows="5" animated />
        </div>

        <div v-else-if="tasks.length === 0" class="empty-state">
          <el-empty description="暂无任务">
            <el-button type="primary" @click="goToUpload">创建第一个审计任务</el-button>
          </el-empty>
        </div>

        <div v-else class="tasks-table">
          <el-table :data="tasks" style="width: 100%" stripe>
            <el-table-column prop="task_name" label="任务名称" min-width="150" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="progress_percentage" label="进度" width="120">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.progress_percentage || 0"
                  :status="getProgressStatus(row.status)"
                  :stroke-width="6"
                />
              </template>
            </el-table-column>
            <el-table-column prop="total_files" label="文件数" width="80" />
            <el-table-column prop="processed_files" label="已处理" width="80" />
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button type="text" @click="viewTask(row.id)">
                  <el-icon><View /></el-icon>
                  查看
                </el-button>
                <el-button
                  v-if="row.status === 'completed'"
                  type="text"
                  @click="downloadReport(row.id)"
                >
                  <el-icon><Download /></el-icon>
                  报告
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="totalTasks"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadTasks"
              @current-change="loadTasks"
            />
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuditStore } from '@/stores/audit'
import { ElMessage } from 'element-plus'
import type { AuditTask } from '@/types/audit'

const router = useRouter()
const route = useRoute()
const auditStore = useAuditStore()

const loading = ref(false)
const tasksLoading = ref(false)
const statistics = ref({
  total_tasks: 0,
  completed_tasks: 0,
  processing_tasks: 0,
  failed_tasks: 0,
  total_contracts: 0,
  total_invoices: 0,
  success_rate: 0
})

const tasks = ref<AuditTask[]>([])
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalTasks = ref(0)

// 加载统计数据
const loadStatistics = async () => {
  loading.value = true
  try {
    statistics.value = await auditStore.getStatistics()
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

// 加载任务列表
const loadTasks = async () => {
  tasksLoading.value = true
  try {
    const result = await auditStore.getTasks({
      page: currentPage.value,
      size: pageSize.value,
      status: statusFilter.value
    })
    tasks.value = result.data
    totalTasks.value = result.total
  } catch (error) {
    console.error('加载任务列表失败:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    tasksLoading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  loadStatistics()
  loadTasks()
}

// 页面导航
const goBack = () => {
  router.push('/audit')
}

const goToUpload = () => {
  router.push('/audit/upload')
}

const viewTask = (taskId: string) => {
  router.push(`/audit/processing/${taskId}`)
}

const downloadReport = async (taskId: string) => {
  try {
    // 这里应该调用下载报告的API
    ElMessage.info('报告下载功能开发中...')
  } catch (error) {
    console.error('下载报告失败:', error)
    ElMessage.error('下载报告失败')
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

const formatTime = (time: string) => {
  return new Date(time).toLocaleString()
}

// 生命周期
onMounted(() => {
  loadStatistics()
  loadTasks()
})
</script>

<style scoped>
.results-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.results-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.back-button {
  font-size: 1rem;
}

.results-header h2 {
  font-size: 1.8rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.card-header > div {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.overview-card {
  margin-bottom: 2rem;
}

.loading-container {
  padding: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.stat-card:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.success {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.stat-icon.processing {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.failed {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
}

.stat-icon.contracts {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.invoices {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-icon.rate {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
  margin-bottom: 0.25rem;
}

.stat-label {
  color: #6b7280;
  font-size: 0.9rem;
}

.tasks-card {
  margin-bottom: 2rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.empty-state {
  text-align: center;
  padding: 3rem;
}

.tasks-table {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

@media (max-width: 768px) {
  .results-container {
    padding: 1rem;
  }

  .results-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }

  .stat-card {
    padding: 1rem;
  }

  .stat-number {
    font-size: 1.5rem;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }

  .header-actions {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }

  .header-actions .el-select {
    width: 100%;
  }
}
</style>