<template>
  <div class="upload-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>审计管理</el-breadcrumb-item>
        <el-breadcrumb-item>文件上传</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="header-content">
        <h1 class="page-title">文件上传</h1>
        <p class="page-description">上传包含合同和发票的ZIP文件开始审计</p>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <el-row :gutter="24">
        <!-- 左侧：文件上传区域 -->
        <el-col :lg="16" :md="24" :sm="24">
          <el-card class="upload-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="header-icon">📤</span>
                <span class="header-title">文件上传</span>
              </div>
            </template>

            <!-- 拖拽上传区域 -->
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :show-file-list="false"
              accept=".zip"
              :on-change="handleFileChange"
              :before-upload="beforeUpload"
              drag
              class="upload-component"
            >
                <div class="upload-content">
                  <!-- 未上传状态 -->
                  <div v-if="!uploadedFile" class="upload-placeholder">
                    <span class="upload-icon">☁️</span>
                    <h3 class="upload-title">拖拽ZIP文件到此处</h3>
                    <p class="upload-subtitle">或者点击选择文件</p>
                    <p class="upload-hint">
                      支持格式：ZIP（包含1份合同和多份发票）<br>
                      最大文件大小：50MB
                    </p>
                  </div>

                  <!-- 上传中状态 -->
                  <div v-else-if="uploadStatus === 'uploading'" class="upload-progress">
                    <span class="upload-icon rotating">⏳</span>
                    <h3 class="upload-title">正在上传...</h3>
                    <p class="upload-subtitle">{{ uploadedFile.name }}</p>
                    <el-progress
                      :percentage="uploadProgress"
                      :stroke-width="8"
                      class="progress-bar"
                    />
                    <p class="upload-hint">{{ uploadProgress }}% 完成</p>
                  </div>

                  <!-- 上传成功状态 -->
                  <div v-else-if="uploadStatus === 'success'" class="upload-success">
                    <span class="upload-icon success">✅</span>
                    <h3 class="upload-title">上传成功</h3>
                    <p class="upload-subtitle">{{ uploadedFile.name }}</p>
                    <p class="upload-hint">文件大小：{{ formatFileSize(uploadedFile.size) }}</p>
                  </div>

                  <!-- 上传失败状态 -->
                  <div v-else-if="uploadStatus === 'error'" class="upload-error">
                    <span class="upload-icon error">❌</span>
                    <h3 class="upload-title">上传失败</h3>
                    <p class="upload-subtitle">{{ errorMessage }}</p>
                    <el-button type="primary" @click="retryUpload">重新上传</el-button>
                  </div>
                </div>
            </el-upload>

            <!-- 文件预览区域 -->
            <div v-if="uploadedFile && uploadStatus === 'success'" class="file-preview">
              <div class="preview-header">
                <h4>文件预览</h4>
                <el-button
                  type="danger"
                  circle
                  @click="removeFile"
                >
                  🗑️
                </el-button>
              </div>

              <div class="preview-content">
                <div class="file-info">
                  <span class="file-icon">📄</span>
                  <div class="file-details">
                    <p class="file-name">{{ uploadedFile.name }}</p>
                    <p class="file-meta">
                      大小：{{ formatFileSize(uploadedFile.size) }} |
                      类型：{{ getFileType(uploadedFile.name) }}
                    </p>
                  </div>
                </div>

                <!-- 解压文件列表 -->
                <div v-if="extractedFiles.length > 0" class="extracted-files">
                  <h5>解压文件列表：</h5>
                  <div class="file-list">
                    <div
                      v-for="file in extractedFiles"
                      :key="file.id"
                      class="file-item"
                      :class="{ 'is-contract': file.category === 'contract' }"
                    >
                      <span class="item-icon">
                        {{ file.category === 'contract' ? '📋' : '🧾' }}
                      </span>
                      <span class="item-name">{{ file.name }}</span>
                      <el-tag
                        :type="getFileTypeTag(file.category)"
                        size="small"
                      >
                        {{ getCategoryLabel(file.category) }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="action-buttons">
              <el-button
                type="primary"
                size="large"
                :disabled="!canStartAudit"
                :loading="isStartingAudit"
                @click="startAudit"
              >
                ▶️
                开始审计
              </el-button>
              <el-button
                size="large"
                @click="clearAll"
                :disabled="isStartingAudit"
              >
                🔄
                清除所有
              </el-button>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：说明面板 -->
        <el-col :lg="8" :md="24" :sm="24">
          <el-card class="instruction-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="header-icon">ℹ️</span>
                <span class="header-title">上传说明</span>
              </div>
            </template>

            <div class="instruction-content">
              <div class="instruction-section">
                <h4>
                  📄
                  支持格式
                </h4>
                <ul>
                  <li>ZIP压缩包</li>
                  <li>内含PDF、JPG、PNG格式的合同和发票文件</li>
                </ul>
              </div>

              <div class="instruction-section">
                <h4>
                  📁
                  文件限制
                </h4>
                <ul>
                  <li>ZIP文件大小：≤ 50MB</li>
                  <li>合同文件：1份</li>
                  <li>发票文件：多份</li>
                </ul>
              </div>

              <div class="instruction-section">
                <h4>
                  ✏️
                  命名规范
                </h4>
                <p>建议使用清晰的文件名，便于识别</p>
                <ul>
                  <li>合同：合同_采购方_供应商.pdf</li>
                  <li>发票：发票_001_日期.pdf</li>
                </ul>
              </div>

              <div class="instruction-section">
                <h4>
                  ⬇️
                  示例文件
                </h4>
                <el-button
                  type="primary"
                  plain
                  size="small"
                  @click="downloadSample"
                >
                  下载示例
                </el-button>
                <p class="sample-hint">下载标准的示例文件进行测试</p>
              </div>

              <div class="instruction-section">
                <h4>
                  ⚠️
                  注意事项
                </h4>
                <ul>
                  <li>确保文件清晰可读</li>
                  <li>避免文件损坏或密码保护</li>
                  <li>检查文件完整性</li>
                </ul>
              </div>
            </div>
          </el-card>

          <!-- 上传历史 -->
          <el-card class="history-card" shadow="hover" v-if="uploadHistory.length > 0">
            <template #header>
              <div class="card-header">
                <span class="header-icon">🕐</span>
                <span class="header-title">上传历史</span>
              </div>
            </template>

            <div class="history-content">
              <div
                v-for="item in uploadHistory.slice(0, 5)"
                :key="item.id"
                class="history-item"
              >
                <div class="history-info">
                  <p class="history-name">{{ item.name }}</p>
                  <p class="history-time">{{ formatTime(item.createdAt) }}</p>
                </div>
                <el-tag :type="getStatusType(item.status)" size="small">
                  {{ getStatusLabel(item.status) }}
                </el-tag>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
// import {
//   Upload,
//   CloudUpload,
//   Loading,
//   Check,
//   Close,
//   Delete,
//   Play,
//   Refresh,
//   Document,
//   Invoice,
//   InfoFilled,
//   FolderOpened,
//   Edit,
//   Download,
//   Warning,
//   Clock
// } from '@element-plus/icons-vue'
import { useAuditStore, type FileInfo } from '@/stores/audit'
import { apiService } from '@/services/api'

const router = useRouter()
const auditStore = useAuditStore()

// 响应式数据
const uploadRef = ref()
const uploadedFile = ref<File | null>(null)
const uploadStatus = ref<'idle' | 'uploading' | 'success' | 'error'>('idle')
const uploadProgress = ref(0)
const errorMessage = ref('')
const extractedFiles = ref<FileInfo[]>([])
const isStartingAudit = ref(false)
const uploadHistory = ref<any[]>([])

// 计算属性
const contractCount = computed(() => extractedFiles.value.filter(file => file.category === 'contract').length)
const invoiceCount = computed(() => extractedFiles.value.filter(file => file.category === 'invoice').length)
const hasWarnings = computed(() => {
  const warnings: string[] = []
  if (contractCount.value !== 1) warnings.push(`识别到${contractCount.value}份合同，建议上传前确认ZIP中仅包含1份合同`)
  if (invoiceCount.value < 1) warnings.push('未识别到发票文件')
  return warnings.length > 0
})
const canStartAudit = computed(() => {
  const totalFiles = contractCount.value + invoiceCount.value
  return uploadedFile.value && uploadStatus.value === 'success' && totalFiles >= 2
})

const handleFileChange = (file: any) => {
  if (validateFile(file.raw)) {
    uploadedFile.value = file.raw
    startUpload()
  }
}

const beforeUpload = (file: File) => {
  if (!validateFile(file)) {
    return false
  }
  return false // 阻止自动上传
}

const validateFile = (file: File): boolean => {
  // 检查文件类型
  if (!file.name.toLowerCase().endsWith('.zip')) {
    ElMessage.error('只支持ZIP文件格式')
    return false
  }

  // 检查文件大小
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过50MB')
    return false
  }

  return true
}

const startUpload = async () => {
  if (!uploadedFile.value) return

  uploadStatus.value = 'uploading'
  uploadProgress.value = 0
  errorMessage.value = ''

  try {
    const formData = new FormData()
    formData.append('file', uploadedFile.value)
    formData.append('task_name', `审计任务-${new Date().getTime()}`)

    const result = await apiService.upload('/upload/zip', formData, (progress) => {
      uploadProgress.value = progress
    })

    uploadStatus.value = 'success'
    extractedFiles.value = result.files || []

    // 添加到上传历史
    uploadHistory.value.unshift({
      id: result.task_id,
      name: uploadedFile.value?.name,
      size: uploadedFile.value?.size || 0,
      status: 'uploaded',
      createdAt: new Date()
    })

    const warnings = result.summary?.warnings || result.task?.summary?.warnings || []
    if (warnings.length > 0) {
      ElMessage.warning(warnings.join('；'))
    } else {
      ElMessage.success('文件上传成功')
    }
  } catch (error: any) {
    uploadStatus.value = 'error'
    errorMessage.value = error.message || '上传失败'
    ElMessage.error('文件上传失败')
  }
}

const removeFile = () => {
  uploadedFile.value = null
  uploadStatus.value = 'idle'
  uploadProgress.value = 0
  errorMessage.value = ''
  extractedFiles.value = []
}

const clearAll = () => {
  removeFile()
  uploadHistory.value = []
}

const retryUpload = () => {
  if (uploadedFile.value) {
    startUpload()
  }
}

const startAudit = async () => {
  if (!canStartAudit.value) return

  // 如果有分类警告，弹窗确认
  if (hasWarnings.value) {
    try {
      await ElMessageBox.confirm(
        `文件分类结果：${contractCount.value}份合同、${invoiceCount.value}份发票。系统将在审计过程中通过内容识别进一步确认文件类型，是否继续？`,
        '文件分类提示',
        {
          confirmButtonText: '继续审计',
          cancelButtonText: '取消',
          type: 'warning',
          distinguishCancelAndClose: true,
        }
      )
    } catch {
      // 用户取消
      return
    }
  }

  try {
    isStartingAudit.value = true

    // 获取当前上传任务的任务ID
    const taskId = uploadHistory.value[0]?.id
    if (!taskId) {
      throw new Error('未找到有效的任务ID，请重新上传文件')
    }

    // 创建审计任务
    const task = auditStore.createTask(
      `审计任务-${taskId}`,
      extractedFiles.value
    )

    // 开始审计
    await apiService.post('/audit/start', {
      task_id: taskId,
      audit_config: {
        enable_duplicate_detection: true,
        enable_amount_validation: true,
        enable_content_matching: true,
        confidence_threshold: 0.8
      }
    })

    // 跳转到进度页面
    router.push(`/audit/processing/${taskId}`)

  } catch (error: any) {
    ElMessage.error('启动审计失败: ' + (error.message || '未知错误'))
  } finally {
    isStartingAudit.value = false
  }
}

const downloadSample = () => {
  apiService.download('/upload/sample', 'sample_contract_invoice_audit.zip')
    .then(() => {
      ElMessage.success('示例文件下载成功')
    })
    .catch((error: any) => {
      ElMessage.error('示例文件下载失败: ' + (error.message || '未知错误'))
    })
}

// 工具函数
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getFileType = (filename: string): string => {
  const ext = filename.toLowerCase().split('.').pop()
  const typeMap: Record<string, string> = {
    'pdf': 'PDF文档',
    'jpg': 'JPEG图片',
    'jpeg': 'JPEG图片',
    'png': 'PNG图片',
    'zip': 'ZIP压缩包'
  }
  return ext ? typeMap[ext] || '未知文件' : '未知文件'
}


const getFileTypeTag = (category: string) => {
  return category === 'contract' ? 'primary' : 'success'
}

const getCategoryLabel = (category: string) => {
  return category === 'contract' ? '合同' : '发票'
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'uploaded': 'success',
    'processing': 'warning',
    'completed': 'info',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    'uploaded': '已上传',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return labelMap[status] || status
}

const formatTime = (date: Date): string => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`

  const days = Math.floor(hours / 24)
  return `${days}天前`
}
</script>

<style scoped>
.upload-page {
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

.upload-card {
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

.upload-component {
  margin-bottom: 24px;
}

.upload-component :deep(.el-upload-dragger) {
  border: 2px dashed #DCDFE6;
  border-radius: 8px;
  padding: 48px 24px;
  background-color: transparent;
  transition: all 0.3s ease;
}

.upload-component :deep(.el-upload-dragger:hover) {
  border-color: #409EFF;
  background-color: #F5F7FA;
}

.upload-component :deep(.el-upload-dragger.is-dragover) {
  border-color: #409EFF;
  background-color: #ECF5FF;
  transform: scale(1.02);
}

.upload-icon {
  font-size: 48px;
  color: #C0C4CC;
  margin-bottom: 16px;
}

.upload-icon.success {
  color: #67C23A;
}

.upload-icon.error {
  color: #F56C6C;
}

.upload-icon.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.upload-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.upload-subtitle {
  font-size: 14px;
  color: #606266;
  margin-bottom: 16px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
  margin: 0;
}

.progress-bar {
  margin: 16px 0;
}

.file-preview {
  border-top: 1px solid #EBEEF5;
  padding-top: 24px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.preview-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.preview-content {
  margin-bottom: 24px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background-color: #F5F7FA;
  border-radius: 8px;
  margin-bottom: 16px;
}

.file-icon {
  font-size: 24px;
  color: #409EFF;
}

.file-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.file-meta {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

.extracted-files {
  margin-top: 16px;
}

.extracted-files h5 {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #FAFAFA;
  border-radius: 6px;
  border-left: 3px solid #E4E7ED;
  transition: all 0.2s ease;
}

.file-item:hover {
  background-color: #F5F7FA;
}

.file-item.is-contract {
  border-left-color: #409EFF;
}

.item-icon {
  font-size: 16px;
  color: #909399;
}

.item-name {
  flex: 1;
  font-size: 13px;
  color: #303133;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.instruction-card,
.history-card {
  margin-bottom: 24px;
}

.instruction-content {
  margin-top: 16px;
}

.instruction-section {
  margin-bottom: 24px;
}

.instruction-section:last-child {
  margin-bottom: 0;
}

.instruction-section h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.instruction-section p {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 12px;
}

.instruction-section ul {
  margin: 0;
  padding-left: 20px;
}

.instruction-section li {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

.sample-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.history-content {
  margin-top: 16px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #F0F0F0;
}

.history-item:last-child {
  border-bottom: none;
}

.history-name {
  font-size: 13px;
  color: #303133;
  margin-bottom: 2px;
}

.history-time {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

@media (max-width: 768px) {
  .upload-page {
    padding: 16px;
  }

  .page-title {
    font-size: 24px;
  }

  .upload-zone {
    padding: 32px 16px;
  }

  .action-buttons {
    flex-direction: column;
  }
}
</style>
