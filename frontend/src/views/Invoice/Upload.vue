<template>
  <div class="upload-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>发票识别</el-breadcrumb-item>
        <el-breadcrumb-item>文件上传</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="header-content">
        <h1 class="page-title">发票识别</h1>
        <p class="page-description">上传发票文件，快速提取关键信息</p>
      </div>
    </div>

    <div class="main-content">
      <el-row :gutter="24">
        <el-col :lg="16" :md="24" :sm="24">
          <el-card class="upload-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="header-icon">🧾</span>
                <span class="header-title">上传发票</span>
              </div>
            </template>

            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :show-file-list="false"
              accept=".pdf,.jpg,.jpeg,.png"
              multiple
              :on-change="handleFileChange"
              drag
              class="upload-component"
            >
              <div class="upload-content">
                <div v-if="selectedFiles.length === 0" class="upload-placeholder">
                  <span class="upload-icon">☁️</span>
                  <h3 class="upload-title">拖拽发票文件到此处</h3>
                  <p class="upload-subtitle">或者点击选择文件（支持多选）</p>
                  <p class="upload-hint">
                    支持格式：PDF、JPG、PNG<br>
                    单次最多上传50个文件
                  </p>
                </div>
                <div v-else class="upload-has-files">
                  <span class="upload-icon">📄</span>
                  <h3 class="upload-title">已选择 {{ selectedFiles.length }} 个文件</h3>
                  <p class="upload-subtitle">点击或拖拽继续添加文件</p>
                </div>
              </div>
            </el-upload>

            <!-- 文件列表 -->
            <div v-if="selectedFiles.length > 0" class="file-list-section">
              <div class="file-list-header">
                <h4>文件列表 ({{ selectedFiles.length }})</h4>
                <el-button type="danger" plain size="small" @click="clearFiles">清空全部</el-button>
              </div>
              <div class="file-list">
                <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
                  <span class="file-icon">{{ getFileIcon(file.name) }}</span>
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                  <el-button
                    v-if="file.type.startsWith('image/') || file.name.toLowerCase().endsWith('.pdf')"
                    circle
                    size="small"
                    class="preview-btn"
                    @click="previewLocalFile(file)"
                  >
                    <el-icon><View /></el-icon>
                  </el-button>
                  <el-button circle size="small" type="danger" @click="removeFile(index)">
                    <el-icon><Close /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="action-buttons" v-if="selectedFiles.length > 0">
              <el-button
                type="primary"
                size="large"
                :disabled="isUploading"
                :loading="isUploading"
                @click="uploadAndStart"
              >
                上传并开始识别
              </el-button>
              <el-button
                size="large"
                @click="clearFiles"
                :disabled="isUploading"
              >
                清除所有
              </el-button>
            </div>
          </el-card>
        </el-col>

        <el-col :lg="8" :md="24" :sm="24">
          <el-card class="instruction-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="header-icon">ℹ️</span>
                <span class="header-title">使用说明</span>
              </div>
            </template>

            <div class="instruction-content">
              <div class="instruction-section">
                <h4>📄 支持格式</h4>
                <ul>
                  <li>PDF 文档</li>
                  <li>JPG / JPEG 图片</li>
                  <li>PNG 图片</li>
                </ul>
              </div>

              <div class="instruction-section">
                <h4>📁 文件要求</h4>
                <ul>
                  <li>单次最多上传 50 个文件</li>
                  <li>确保图片清晰可读</li>
                  <li>建议分辨率不低于 300dpi</li>
                </ul>
              </div>

              <div class="instruction-section">
                <h4>📊 识别内容</h4>
                <ul>
                  <li>发票号码、开票日期</li>
                  <li>销售方 / 购买方信息</li>
                  <li>价税合计、税额、税率</li>
                  <li>商品清单明细</li>
                </ul>
              </div>

              <div class="instruction-section">
                <h4>💡 温馨提示</h4>
                <ul>
                  <li>支持增值税发票、普通发票</li>
                  <li>识别结果可导出 Excel</li>
                  <li>识别完成后可预览原文件</li>
                </ul>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 本地文件预览弹窗 -->
    <el-dialog
      v-model="localPreviewVisible"
      title="文件预览"
      width="80%"
      top="5vh"
      destroy-on-close
    >
      <div class="local-preview-container">
        <iframe
          v-if="localPreviewUrl && isLocalPreviewPDF"
          :src="localPreviewUrl"
          class="preview-iframe"
          frameborder="0"
        />
        <el-image
          v-else-if="localPreviewUrl"
          :src="localPreviewUrl"
          :preview-src-list="[localPreviewUrl]"
          fit="contain"
          class="preview-image"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { View, Close } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

const router = useRouter()

const uploadRef = ref()
const selectedFiles = ref<File[]>([])
const isUploading = ref(false)

// 本地预览
const localPreviewVisible = ref(false)
const localPreviewUrl = ref('')
const localPreviewFileName = ref('')

const isLocalPreviewPDF = ref(false)

const handleFileChange = (file: any) => {
  const raw = file.raw as File
  if (!raw) return

  const ext = raw.name.toLowerCase()
  if (!ext.endsWith('.pdf') && !ext.endsWith('.jpg') && !ext.endsWith('.jpeg') && !ext.endsWith('.png')) {
    ElMessage.warning(`不支持的文件类型: ${raw.name}`)
    return
  }

  if (selectedFiles.value.length >= 50) {
    ElMessage.warning('单次最多上传50个文件')
    return
  }

  selectedFiles.value.push(raw)
}

const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
}

const clearFiles = () => {
  selectedFiles.value = []
  uploadRef.value?.clearFiles()
}

const previewLocalFile = (file: File) => {
  localPreviewUrl.value = URL.createObjectURL(file)
  localPreviewFileName.value = file.name
  isLocalPreviewPDF.value = file.name.toLowerCase().endsWith('.pdf')
  localPreviewVisible.value = true
}

const getFileIcon = (name: string) => {
  if (name.toLowerCase().endsWith('.pdf')) return '📕'
  return '🖼️'
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const uploadAndStart = async () => {
  if (selectedFiles.value.length === 0) return

  try {
    isUploading.value = true

    const formData = new FormData()
    selectedFiles.value.forEach((file) => {
      formData.append('files', file)
    })
    formData.append('task_name', `发票识别-${new Date().toLocaleDateString()}`)

    const result = await apiService.upload('/upload/invoice-batch', formData)

    ElMessage.success(`上传成功，共 ${result.file_count} 个文件`)

    // 启动OCR识别
    await apiService.post('/ocr/start', { task_id: result.task_id })

    router.push(`/invoice/processing/${result.task_id}`)
  } catch (error: any) {
    ElMessage.error('上传失败: ' + (error.message || '未知错误'))
  } finally {
    isUploading.value = false
  }
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
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.upload-component :deep(.el-upload-dragger) {
  border: 2px dashed #DCDFE6;
  border-radius: 8px;
  padding: 32px 24px;
  transition: all 0.3s ease;
}

.upload-component :deep(.el-upload-dragger:hover) {
  border-color: #409EFF;
  background-color: #F5F7FA;
}

.upload-icon {
  font-size: 48px;
  color: #C0C4CC;
  margin-bottom: 16px;
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

.file-list-section {
  margin-top: 24px;
  border-top: 1px solid #EBEEF5;
  padding-top: 24px;
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.file-list-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 320px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #FAFAFA;
  border-radius: 6px;
}

.file-icon {
  font-size: 18px;
}

.file-name {
  flex: 1;
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.preview-btn {
  opacity: 0.6;
}

.preview-btn:hover {
  opacity: 1;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 24px;
}

.instruction-card {
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

.instruction-section ul {
  margin: 0;
  padding-left: 20px;
}

.instruction-section li {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

.local-preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  max-height: 70vh;
  overflow: auto;
}

.preview-iframe {
  width: 100%;
  height: 70vh;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
}

.preview-image {
  max-width: 100%;
  max-height: 70vh;
}

@media (max-width: 768px) {
  .upload-page {
    padding: 16px;
  }

  .page-title {
    font-size: 24px;
  }

  .action-buttons {
    flex-direction: column;
  }
}
</style>
