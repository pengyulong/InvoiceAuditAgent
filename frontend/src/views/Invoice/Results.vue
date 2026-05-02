<template>
  <div class="results-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: '/invoice/upload' }">发票识别</el-breadcrumb-item>
        <el-breadcrumb-item>识别结果</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="header-content">
        <h1 class="page-title">发票识别结果</h1>
        <p class="page-description">查看发票信息提取结果</p>
      </div>
    </div>

    <div class="main-content" v-if="results">
      <!-- 摘要卡片 -->
      <el-card class="summary-card" shadow="hover">
        <div class="summary-content">
          <el-row :gutter="24">
            <el-col :span="6" v-for="metric in metrics" :key="metric.key">
              <div class="metric-item">
                <div class="metric-icon" :style="{ background: metric.color }">
                  {{ metric.icon }}
                </div>
                <div class="metric-info">
                  <h3>{{ metric.value }}</h3>
                  <p>{{ metric.label }}</p>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- 发票列表 -->
      <el-card class="invoices-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="header-icon">🧾</span>
            <span class="header-title">发票列表</span>
            <div class="header-actions">
              <el-button type="primary" size="small" @click="exportExcel" :loading="isExporting">
                导出Excel
              </el-button>
              <el-button type="info" size="small" @click="exportJSON" :loading="isExportingJSON">
                导出JSON
              </el-button>
              <el-button size="small" @click="goBack">
                返回上传
              </el-button>
            </div>
          </div>
        </template>

        <el-table :data="invoices" stripe empty-text="暂无识别结果" max-height="600">
          <el-table-column prop="invoice_number" label="发票号码" width="160" />
          <el-table-column prop="invoice_date" label="开票日期" width="120" />
          <el-table-column prop="seller_name" label="销售方" min-width="180" show-overflow-tooltip />
          <el-table-column prop="buyer_name" label="购买方" min-width="180" show-overflow-tooltip />
          <el-table-column label="价税合计" width="130" align="right">
            <template #default="{ row }">
              <span v-if="row.total_amount">¥{{ formatCurrency(row.total_amount) }}</span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column label="税额" width="110" align="right">
            <template #default="{ row }">
              <span v-if="row.tax_amount">¥{{ formatCurrency(row.tax_amount) }}</span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column label="税率" width="80" align="center">
            <template #default="{ row }">
              {{ formatTaxRate(row.tax_rate) }}
            </template>
          </el-table-column>
          <el-table-column label="置信度" width="90" align="center">
            <template #default="{ row }">
              <el-tag
                :type="row.error ? 'danger' : (row.confidence_score >= 0.8 ? 'success' : 'warning')"
                size="small"
              >
                {{ row.error ? '失败' : ((row.confidence_score || 0) * 100).toFixed(0) + '%' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.source_file"
                circle
                size="small"
                @click="openPreview(row)"
              >
                <el-icon><View /></el-icon>
              </el-button>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 商品明细 -->
      <el-card class="items-card" shadow="hover" v-if="hasItems">
        <template #header>
          <div class="card-header">
            <span class="header-icon">📦</span>
            <span class="header-title">商品明细汇总</span>
          </div>
        </template>

        <el-table :data="allItems" stripe empty-text="发票未提取到商品清单">
          <el-table-column prop="invoice_number" label="来源发票" width="160" />
          <el-table-column prop="name" label="商品名称" min-width="150" />
          <el-table-column prop="specification" label="规格型号" width="120" />
          <el-table-column prop="unit" label="单位" width="60" />
          <el-table-column prop="quantity" label="数量" width="80" align="center" />
          <el-table-column label="单价" width="100" align="right">
            <template #default="{ row }">
              ¥{{ formatCurrency(row.unit_price) }}
            </template>
          </el-table-column>
          <el-table-column label="金额" width="110" align="right">
            <template #default="{ row }">
              ¥{{ formatCurrency(row.amount) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <div v-else class="loading-container">
      <el-skeleton animated>
        <template #template>
          <el-skeleton-item variant="text" style="width: 30%" />
          <el-skeleton-item variant="text" style="width: 60%; margin-top: 10px" />
        </template>
      </el-skeleton>
    </div>

    <!-- 文件预览弹窗 -->
    <FilePreviewDialog
      v-model="previewDialogVisible"
      :file-path="previewFilePath"
      :file-name="previewFileName"
      :file-type="previewFileType"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { View } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'
import FilePreviewDialog from '@/components/FilePreviewDialog.vue'

const router = useRouter()
const route = useRoute()

const taskId = ref(route.params.taskId as string)
const results = ref<any>(null)
const loading = ref(true)
const isExporting = ref(false)
const isExportingJSON = ref(false)

// 预览
const previewDialogVisible = ref(false)
const previewFilePath = ref('')
const previewFileName = ref('')
const previewFileType = ref('')

const invoices = computed(() => results.value?.invoices || [])
const hasItems = computed(() =>
  invoices.value.some((inv: any) => inv.product_list?.length > 0)
)
const allItems = computed(() => {
  const items: any[] = []
  invoices.value.forEach((inv: any) => {
    (inv.product_list || []).forEach((item: any) => {
      items.push({ ...item, invoice_number: inv.invoice_number || inv.file_name || '未知' })
    })
  })
  return items
})

const metrics = computed(() => {
  const total = invoices.value.length
  const success = invoices.value.filter((i: any) => !i.error).length
  const fail = total - success
  const totalAmount = invoices.value.reduce((sum: number, i: any) => sum + (Number(i.total_amount) || 0), 0)
  return [
    { key: 'total', icon: '📄', label: '发票总数', value: total, color: 'linear-gradient(135deg, #667eea, #764ba2)' },
    { key: 'success', icon: '✅', label: '识别成功', value: success, color: 'linear-gradient(135deg, #4facfe, #00f2fe)' },
    { key: 'fail', icon: '❌', label: '识别失败', value: fail, color: 'linear-gradient(135deg, #fa709a, #fee140)' },
    { key: 'amount', icon: '💰', label: '总金额', value: `¥${formatCurrency(totalAmount)}`, color: 'linear-gradient(135deg, #f093fb, #f5576c)' },
  ]
})

const loadResults = async () => {
  try {
    loading.value = true
    const data = await apiService.get(`/ocr/${taskId.value}/results`)
    results.value = data
  } catch (error: any) {
    ElMessage.error('加载结果失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const openPreview = (row: any) => {
  previewFilePath.value = row.source_file || ''
  previewFileName.value = row.file_name || row.source_file?.split('/').pop() || '文件'
  previewFileType.value = row.source_file?.endsWith('.pdf') ? 'application/pdf' : 'image/'
  previewDialogVisible.value = true
}

const exportExcel = async () => {
  try {
    isExporting.value = true
    await apiService.download(`/results/${taskId.value}/export/invoice-excel`, `invoice_report_${taskId.value}.xlsx`)
    ElMessage.success('Excel导出成功')
  } catch (error: any) {
    ElMessage.error('导出失败: ' + (error.message || '未知错误'))
  } finally {
    isExporting.value = false
  }
}

const exportJSON = async () => {
  try {
    isExportingJSON.value = true
    const data = JSON.stringify(results.value, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `invoice_data_${taskId.value}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('JSON导出成功')
  } catch (error: any) {
    ElMessage.error('导出失败: ' + (error.message || '未知错误'))
  } finally {
    isExportingJSON.value = false
  }
}

const goBack = () => {
  router.push('/invoice/upload')
}

const formatCurrency = (amount: number): string => {
  const value = Number(amount) || 0
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatTaxRate = (rate: number | string | null | undefined): string => {
  if (rate === null || rate === undefined || rate === '') return '-'
  const value = Number(rate) || 0
  return value > 1 ? `${value.toFixed(0)}%` : `${(value * 100).toFixed(0)}%`
}

onMounted(() => {
  if (!taskId.value) {
    ElMessage.error('缺少任务ID')
    router.push('/invoice/upload')
    return
  }
  loadResults()
})
</script>

<style scoped>
.results-page {
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

.summary-card {
  margin-bottom: 24px;
}

.summary-content {
  padding: 8px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
  flex-shrink: 0;
}

.metric-info h3 {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 2px;
}

.metric-info p {
  font-size: 13px;
  color: #909399;
  margin: 0;
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

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.invoices-card {
  margin-bottom: 24px;
}

.items-card {
  margin-bottom: 24px;
}

.text-muted {
  color: #C0C4CC;
}

.loading-container {
  padding: 24px;
}

@media (max-width: 768px) {
  .results-page {
    padding: 16px;
  }

  .page-title {
    font-size: 24px;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
