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
                <el-icon class="header-icon"><Document /></el-icon>
                <span class="header-title">上传发票</span>
              </div>
            </template>

            <div class="upload-summary">
              <div class="upload-summary-main">
                <div class="summary-title">批量发票识别</div>
                <div class="summary-subtitle">
                  选择 PDF 或图片后直接开始识别，系统会自动保留任务和原文件。
                </div>
              </div>
              <div class="upload-summary-stats">
                <div class="summary-stat">
                  <el-icon><Document /></el-icon>
                  <span>{{ selectedFiles.length }} 个文件</span>
                </div>
                <div class="summary-stat">
                  <el-icon><DataLine /></el-icon>
                  <span>{{ totalSelectedSizeLabel }}</span>
                </div>
                <div class="summary-stat">
                  <el-icon><Timer /></el-icon>
                  <span>单次最多 {{ MAX_FILE_COUNT }} 个</span>
                </div>
              </div>
            </div>

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
                  <div class="upload-icon-wrap">
                    <el-icon class="upload-icon"><UploadFilled /></el-icon>
                  </div>
                  <h3 class="upload-title">拖拽发票文件到此处</h3>
                  <p class="upload-subtitle">或点击选择文件</p>
                  <div class="upload-hint-row">
                    <el-tag size="small" effect="plain">PDF</el-tag>
                    <el-tag size="small" effect="plain">JPG / JPEG</el-tag>
                    <el-tag size="small" effect="plain">PNG</el-tag>
                  </div>
                </div>
                <div v-else class="upload-has-files">
                  <div class="upload-icon-wrap">
                    <el-icon class="upload-icon"><Document /></el-icon>
                  </div>
                  <h3 class="upload-title">已选择 {{ selectedFiles.length }} 个文件</h3>
                  <p class="upload-subtitle">继续添加文件，或直接开始上传</p>
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
                  <div class="file-main">
                    <span class="file-icon">{{ getFileIcon(file.name) }}</span>
                    <span class="file-name">{{ file.name }}</span>
                  </div>
                  <div class="file-meta">
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
                    <el-button circle size="small" type="danger" plain @click="removeFile(index)">
                      <el-icon><Close /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="isUploading" class="upload-progress-panel">
              <div class="upload-progress-row">
                <span class="upload-progress-label">{{ uploadStage }}</span>
                <span class="upload-progress-value">{{ uploadProgress }}%</span>
              </div>
              <el-progress :percentage="uploadProgress" :stroke-width="10" />
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
                <el-icon class="button-icon"><UploadFilled /></el-icon>
                上传并开始识别
              </el-button>
              <el-button
                size="large"
                @click="clearFiles"
                :disabled="isUploading"
              >
                <el-icon class="button-icon"><RefreshLeft /></el-icon>
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
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { View, Close, UploadFilled, Document, Loading, RefreshLeft, CirclePlus, DataLine, Timer } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

const router = useRouter()

const uploadRef = ref()
const selectedFiles = ref<File[]>([])
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadStage = ref('准备上传')
const MAX_FILE_SIZE = 50 * 1024 * 1024
const MAX_FILE_COUNT = 50

// 本地预览
const localPreviewVisible = ref(false)
const localPreviewUrl = ref('')
const localPreviewFileName = ref('')

const isLocalPreviewPDF = ref(false)
const totalSelectedSize = computed(() =>
  selectedFiles.value.reduce((total, file) => total + file.size, 0)
)

const totalSelectedSizeLabel = computed(() => formatFileSize(totalSelectedSize.value))

const isSupportedFile = (file: File) => {
  const lowerName = file.name.toLowerCase()
  return lowerName.endsWith('.pdf') || lowerName.endsWith('.jpg') || lowerName.endsWith('.jpeg') || lowerName.endsWith('.png')
}

const isDuplicateFile = (file: File) => {
  return selectedFiles.value.some(
    (existing) =>
      existing.name === file.name &&
      existing.size === file.size &&
      existing.lastModified === file.lastModified
  )
}

const handleFileChange = (file: any) => {
  const raw = file.raw as File
  if (!raw) return

  if (!isSupportedFile(raw)) {
    ElMessage.warning(`不支持的文件类型: ${raw.name}`)
    return
  }

  if (raw.size > MAX_FILE_SIZE) {
    ElMessage.warning(`单个文件不能超过 ${formatFileSize(MAX_FILE_SIZE)}`)
    return
  }

  if (selectedFiles.value.length >= MAX_FILE_COUNT) {
    ElMessage.warning(`单次最多上传 ${MAX_FILE_COUNT} 个文件`)
    return
  }

  if (isDuplicateFile(raw)) {
    ElMessage.info(`文件已在列表中: ${raw.name}`)
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
  uploadProgress.value = 0
  uploadStage.value = '准备上传'
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
    uploadProgress.value = 0
    uploadStage.value = '正在上传文件'

    const formData = new FormData()
    selectedFiles.value.forEach((file) => {
      formData.append('files', file, file.name)
    })
    formData.append('task_name', `发票识别-${new Date().toLocaleDateString()}`)

    const result = await apiService.upload(
      '/upload/invoice-batch',
      formData,
      (progress) => {
        uploadProgress.value = Math.min(progress, 95)
        uploadStage.value = progress < 100 ? `文件上传中 ${progress}%` : '文件已上传，正在创建识别任务'
      },
      { timeout: 10 * 60 * 1000, loading: false } as any
    )

    uploadProgress.value = 100
    uploadStage.value = '文件已上传，正在启动识别'
    ElMessage.success(`上传成功，共 ${result.file_count} 个文件`)

    // 启动OCR识别
    await apiService.post('/ocr/start', { task_id: result.task_id }, { timeout: 2 * 60 * 1000, loading: false } as any)

    uploadStage.value = '识别任务已启动'
    router.push(`/invoice/processing/${result.task_id}`)
  } catch (error: any) {
    uploadStage.value = '上传失败'
    if (!error?.response) {
      ElMessage.error('上传失败: ' + (error.message || '未知错误'))
    }
  } finally {
    isUploading.value = false
  }
}
</script>

<style scoped>
.upload-page {
  min-height: 100vh;
  padding: 24px;
  background:
    linear-gradient(180deg, #f8fafc 0%, #f3f7fc 100%);
}

.page-header {
  margin-bottom: 24px;
  padding: 24px;
  border: 1px solid #e6edf6;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
}

.header-content {
  margin-top: 16px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #172033;
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
  border: 1px solid #e6edf6;
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 18px;
  color: #2563eb;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #172033;
}

.upload-summary {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 0 0 20px;
  margin-bottom: 20px;
  border-bottom: 1px solid #edf2f7;
}

.upload-summary-main {
  flex: 1;
  min-width: 0;
}

.summary-title {
  font-size: 18px;
  font-weight: 600;
  color: #172033;
  margin-bottom: 8px;
}

.summary-subtitle {
  color: #5b6575;
  font-size: 14px;
  line-height: 1.6;
}

.upload-summary-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
}

.summary-stat {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  background: #f5f8fc;
  color: #384152;
  font-size: 13px;
  white-space: nowrap;
}

.upload-component {
  display: block;
}

.upload-component :deep(.el-upload-dragger) {
  width: 100%;
  border: 1.5px dashed #c7d3e4;
  border-radius: 8px;
  padding: 28px 24px;
  transition: all 0.3s ease;
  background: linear-gradient(180deg, #fff 0%, #f8fbff 100%);
}

.upload-component :deep(.el-upload-dragger:hover) {
  border-color: #2563eb;
  background: #f5f9ff;
  box-shadow: 0 12px 30px rgba(37, 99, 235, 0.08);
}

.upload-content {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.upload-placeholder,
.upload-has-files {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.upload-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  margin-bottom: 16px;
  border-radius: 8px;
  background: #eaf2ff;
  color: #2563eb;
}

.upload-icon {
  font-size: 34px;
}

.upload-title {
  font-size: 18px;
  font-weight: 600;
  color: #172033;
  margin-bottom: 8px;
}

.upload-subtitle {
  font-size: 14px;
  color: #5b6575;
  margin-bottom: 12px;
}

.upload-hint-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
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
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  background-color: #f8fafc;
  border-radius: 8px;
  border: 1px solid #edf2f7;
}

.file-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.file-icon {
  font-size: 18px;
}

.file-name {
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
  opacity: 0.85;
}

.preview-btn:hover {
  opacity: 1;
}

.upload-progress-panel {
  margin-top: 20px;
  padding: 16px;
  border-radius: 8px;
  background: #f7fbff;
  border: 1px solid #dbe8fb;
}

.upload-progress-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  gap: 12px;
}

.upload-progress-label {
  font-size: 13px;
  color: #35517f;
}

.upload-progress-value {
  font-size: 13px;
  font-weight: 600;
  color: #2563eb;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 24px;
}

.button-icon {
  margin-right: 6px;
}

.instruction-card {
  margin-bottom: 24px;
  border: 1px solid #e6edf6;
  border-radius: 8px;
  background: #fff;
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

  .page-header {
    padding: 18px;
  }

  .page-title {
    font-size: 24px;
  }

  .upload-summary {
    flex-direction: column;
  }

  .upload-summary-stats {
    justify-content: flex-start;
  }

  .upload-content {
    min-height: 180px;
  }

  .file-item {
    align-items: flex-start;
    flex-direction: column;
  }

  .file-meta {
    width: 100%;
    justify-content: flex-end;
  }

  .action-buttons {
    flex-direction: column;
  }
}
</style>
