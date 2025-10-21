<template>
  <div class="upload-container">
    <div class="upload-header">
      <h2>文件上传</h2>
      <p>请上传包含合同和发票的ZIP文件，系统将自动进行分析</p>
    </div>

    <div class="upload-content">
      <!-- ZIP文件上传区域 -->
      <div class="upload-section">
        <el-card class="upload-card">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>上传审计文件</span>
            </div>
          </template>

          <el-upload
            ref="uploadRef"
            class="zip-uploader"
            drag
            :auto-upload="false"
            :show-file-list="false"
            accept=".zip"
            :on-change="handleFileChange"
            :before-upload="beforeUpload"
          >
            <div class="upload-area">
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">
                <p>将ZIP文件拖拽到此处，或<em>点击上传</em></p>
                <p class="upload-tip">支持格式：ZIP（包含1份合同和多份发票），大小不超过50MB</p>
              </div>
            </div>
          </el-upload>

          <!-- 已选择的文件 -->
          <div v-if="selectedFile" class="selected-file">
            <div class="file-info">
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ selectedFile.name }}</span>
              <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
              <el-button type="text" @click="removeFile">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>

          <!-- 上传进度 -->
          <div v-if="uploading" class="upload-progress">
            <el-progress :percentage="uploadProgress" :status="uploadStatus" />
            <p class="progress-text">{{ progressText }}</p>
          </div>

          <!-- 操作按钮 -->
          <div class="upload-actions">
            <el-button
              type="primary"
              size="large"
              :disabled="!selectedFile || uploading"
              :loading="uploading"
              @click="handleUpload"
            >
              <el-icon><Upload /></el-icon>
              {{ uploading ? '上传中...' : '开始上传' }}
            </el-button>
            <el-button size="large" @click="resetUpload">
              <el-icon><RefreshLeft /></el-icon>
              重新选择
            </el-button>
          </div>
        </el-card>
      </div>

      <!-- 上传说明 -->
      <div class="instructions-section">
        <el-card class="instructions-card">
          <template #header>
            <div class="card-header">
              <el-icon><InfoFilled /></el-icon>
              <span>上传说明</span>
            </div>
          </template>

          <div class="instructions-content">
            <div class="instruction-item">
              <div class="instruction-number">1</div>
              <div class="instruction-text">
                <h4>准备文件</h4>
                <p>将1份合同文件和多份发票文件打包成ZIP格式</p>
              </div>
            </div>
            <div class="instruction-item">
              <div class="instruction-number">2</div>
              <div class="instruction-text">
                <h4>文件命名</h4>
                <p>建议使用包含"合同"、"发票"等关键词的文件名，便于系统识别</p>
              </div>
            </div>
            <div class="instruction-item">
              <div class="instruction-number">3</div>
              <div class="instruction-text">
                <h4>支持格式</h4>
                <p>合同和发票支持PDF、JPG、JPEG、PNG格式</p>
              </div>
            </div>
            <div class="instruction-item">
              <div class="instruction-number">4</div>
              <div class="instruction-text">
                <h4>文件质量</h4>
                <p>确保文件清晰可读，避免模糊、倾斜或有遮挡的情况</p>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 上传结果对话框 -->
    <el-dialog
      v-model="showResultDialog"
      title="上传完成"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-if="uploadResult" class="result-content">
        <el-result
          :icon="uploadResult.success ? 'success' : 'error'"
          :title="uploadResult.success ? '文件上传成功' : '文件上传失败'"
          :sub-title="uploadResult.message"
        >
          <template #extra v-if="uploadResult.success">
            <div class="result-details">
              <p><strong>任务ID：</strong>{{ uploadResult.task_id }}</p>
              <p><strong>文件名：</strong>{{ uploadResult.file_name }}</p>
              <p><strong>文件数量：</strong>{{ uploadResult.total_files }} 个文件</p>
            </div>
            <div class="result-actions">
              <el-button type="primary" @click="startAudit">
                开始审计
              </el-button>
              <el-button @click="showResultDialog = false">
                关闭
              </el-button>
            </div>
          </template>
          <template #extra v-else>
            <el-button @click="showResultDialog = false">
              关闭
            </el-button>
          </template>
        </el-result>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { uploadZipFile } from '@/services/audit'
import { useAuditStore } from '@/stores/audit'

const router = useRouter()
const auditStore = useAuditStore()

// 响应式数据
const uploadRef = ref()
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref<'success' | 'exception' | ''>('')
const progressText = ref('')
const showResultDialog = ref(false)

const uploadResult = reactive<{
  success: boolean
  task_id?: string
  file_name?: string
  total_files?: number
  message?: string
}>({
  success: false
})

// 方法
const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    selectedFile.value = file.raw
  }
}

const beforeUpload = (file: File) => {
  // 检查文件类型
  if (!file.name.toLowerCase().endsWith('.zip')) {
    ElMessage.error('只支持ZIP格式文件')
    return false
  }

  // 检查文件大小（50MB）
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过50MB')
    return false
  }

  return false // 阻止自动上传
}

const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = ''
  progressText.value = '正在上传文件...'

  try {
    const response = await uploadZipFile(selectedFile.value, (percent) => {
      uploadProgress.value = percent
      progressText.value = `正在上传文件... ${percent}%`
    })

    if (response.code === 200) {
      uploadProgress.value = 100
      uploadStatus.value = 'success'
      progressText.value = '上传完成'

      // 设置上传结果
      uploadResult.success = true
      uploadResult.task_id = response.data.task_id
      uploadResult.file_name = response.data.file_name
      uploadResult.total_files = response.data.total_files
      uploadResult.message = '文件已成功上传，可以开始审计'

      // 更新store中的任务信息
      auditStore.setCurrentTask({
        id: response.data.task_id,
        task_name: response.data.file_name,
        status: 'pending',
        progress_percentage: 0,
        current_step: '文件上传完成',
        total_files: response.data.total_files,
        processed_files: 0,
        created_at: new Date().toISOString()
      })

      ElMessage.success('文件上传成功')
      showResultDialog.value = true
    }
  } catch (error: any) {
    uploadStatus.value = 'exception'
    progressText.value = '上传失败'

    uploadResult.success = false
    uploadResult.message = error.message || '文件上传失败'

    ElMessage.error('文件上传失败')
  } finally {
    uploading.value = false
  }
}

const removeFile = () => {
  selectedFile.value = null
  uploadProgress.value = 0
  uploadStatus.value = ''
  progressText.value = ''
}

const resetUpload = () => {
  selectedFile.value = null
  uploadProgress.value = 0
  uploadStatus.value = ''
  progressText.value = ''
  uploading.value = false

  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const startAudit = () => {
  showResultDialog.value = false
  if (uploadResult.task_id) {
    router.push(`/audit/processing/${uploadResult.task_id}`)
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style scoped>
.upload-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.upload-header {
  text-align: center;
  margin-bottom: 3rem;
}

.upload-header h2 {
  font-size: 2.5rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.upload-header p {
  color: #6b7280;
  font-size: 1.1rem;
}

.upload-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.upload-card {
  height: fit-content;
}

.zip-uploader {
  width: 100%;
}

.upload-area {
  text-align: center;
  padding: 3rem 2rem;
}

.upload-icon {
  font-size: 4rem;
  color: #6366f1;
  margin-bottom: 1rem;
}

.upload-text p {
  margin: 0.5rem 0;
}

.upload-text em {
  color: #6366f1;
  font-style: normal;
  font-weight: 600;
}

.upload-tip {
  color: #6b7280;
  font-size: 0.9rem;
}

.selected-file {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.file-name {
  flex: 1;
  font-weight: 500;
  color: #1f2937;
}

.file-size {
  color: #6b7280;
  font-size: 0.9rem;
}

.upload-progress {
  margin-top: 1.5rem;
}

.progress-text {
  text-align: center;
  margin-top: 0.5rem;
  color: #6b7280;
  font-size: 0.9rem;
}

.upload-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2rem;
}

.instructions-card {
  height: fit-content;
}

.instructions-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.instruction-item {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.instruction-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #6366f1;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.instruction-text h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.instruction-text p {
  margin: 0;
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.4;
}

.result-content {
  padding: 1rem 0;
}

.result-details {
  background: #f8fafc;
  padding: 1rem;
  border-radius: 0.5rem;
  margin: 1rem 0;
}

.result-details p {
  margin: 0.5rem 0;
  color: #374151;
}

.result-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1.5rem;
}

@media (max-width: 768px) {
  .upload-content {
    grid-template-columns: 1fr;
  }

  .upload-header h2 {
    font-size: 2rem;
  }

  .upload-actions {
    flex-direction: column;
  }
}
</style>