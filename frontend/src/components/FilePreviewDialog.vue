<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :title="fileName"
    width="80%"
    top="5vh"
    destroy-on-close
    @close="handleClose"
  >
    <div class="preview-container">
      <!-- 加载状态 -->
      <div v-if="loading" class="preview-loading">
        <el-icon class="is-loading" :size="48"><Loading /></el-icon>
        <p>正在加载文件...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="preview-error">
        <el-icon :size="48"><WarningFilled /></el-icon>
        <p>{{ error }}</p>
        <el-button @click="loadFile">重新加载</el-button>
      </div>

      <!-- PDF 预览 -->
      <iframe
        v-else-if="isPDF && blobUrl"
        :src="blobUrl"
        class="preview-iframe"
        frameborder="0"
      />

      <!-- 图片预览 -->
      <el-image
        v-else-if="isImage && blobUrl"
        :src="blobUrl"
        :preview-src-list="[blobUrl]"
        :hide-on-click-modal="true"
        fit="contain"
        class="preview-image"
      />

      <!-- 不支持的文件类型 -->
      <div v-else class="preview-unsupported">
        <el-icon :size="48"><Document /></el-icon>
        <p>该文件类型不支持预览</p>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button type="primary" @click="downloadFile">下载文件</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Loading, WarningFilled, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiService } from '@/services/api'
import axios from 'axios'
import { authStorage } from '@/services/api'

const props = defineProps<{
  modelValue: boolean
  filePath: string
  fileName: string
  fileType: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const loading = ref(false)
const error = ref('')
const blobUrl = ref('')

const isPDF = computed(() =>
  props.fileType === 'application/pdf' || props.fileName.toLowerCase().endsWith('.pdf')
)

const isImage = computed(() =>
  props.fileType.startsWith('image/') ||
  /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(props.fileName)
)

const loadFile = async () => {
  if (!props.filePath) return

  loading.value = true
  error.value = ''

  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'}/upload/preview`,
      {
        params: { path: props.filePath },
        responseType: 'blob',
        headers: {
          Authorization: `Bearer ${authStorage.getToken()}`
        }
      }
    )

    // 释放旧 URL
    if (blobUrl.value) {
      URL.revokeObjectURL(blobUrl.value)
    }

    blobUrl.value = URL.createObjectURL(response.data)
  } catch (err: any) {
    const msg = err.response?.data?.detail || err.message || '加载文件失败'
    error.value = typeof msg === 'string' ? msg : '加载文件失败'
  } finally {
    loading.value = false
  }
}

const downloadFile = () => {
  if (!blobUrl.value) return
  const a = document.createElement('a')
  a.href = blobUrl.value
  a.download = props.fileName
  a.click()
}

const handleClose = () => {
  emit('update:modelValue', false)
  if (blobUrl.value) {
    URL.revokeObjectURL(blobUrl.value)
    blobUrl.value = ''
  }
  error.value = ''
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible && props.filePath) {
      loadFile()
    }
  }
)
</script>

<style scoped>
.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  max-height: 70vh;
  overflow: auto;
}

.preview-loading,
.preview-error,
.preview-unsupported {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #909399;
}

.preview-error {
  color: #F56C6C;
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
</style>
