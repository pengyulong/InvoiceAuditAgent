<template>
  <div class="results-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>审计结果</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="header-content">
        <h1 class="page-title">审计结果</h1>
        <p class="page-description">查看详细的审计报告和数据分析</p>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content" v-if="auditResults">
      <!-- 摘要卡片 -->
      <el-card class="summary-card" shadow="hover">
        <div class="summary-content">
          <div class="summary-header">
            <div class="conclusion">
              <el-icon :class="getConclusionIcon(auditResults.summary.status)" class="conclusion-icon">
                <component :is="getConclusionIcon(auditResults.summary.status)" />
              </el-icon>
              <div class="conclusion-text">
                <h2 class="conclusion-title">{{ getConclusionTitle(auditResults.summary.status) }}</h2>
                <p class="conclusion-subtitle">{{ getConclusionSubtitle(auditResults.summary.status) }}</p>
              </div>
            </div>
          </div>

          <!-- 关键指标 -->
          <div class="metrics-grid">
            <div class="metric-item">
              <div class="metric-icon contract">
                <el-icon><Document /></el-icon>
              </div>
              <div class="metric-content">
                <h3 class="metric-value">¥{{ formatCurrency(auditResults.summary.contract_amount) }}</h3>
                <p class="metric-label">合同金额</p>
              </div>
            </div>

            <div class="metric-item">
              <div class="metric-icon invoice">
                <el-icon><Document /></el-icon>
              </div>
              <div class="metric-content">
                <h3 class="metric-value">¥{{ formatCurrency(auditResults.summary.invoice_total) }}</h3>
                <p class="metric-label">发票总额</p>
              </div>
            </div>

            <div class="metric-item">
              <div class="metric-icon coverage">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="metric-content">
                <h3 class="metric-value">{{ (auditResults.summary.coverage * 100).toFixed(1) }}%</h3>
                <p class="metric-label">覆盖率</p>
              </div>
            </div>

            <div class="metric-item">
              <div class="metric-icon issues">
                <el-icon><Warning /></el-icon>
              </div>
              <div class="metric-content">
                <h3 class="metric-value">{{ auditResults.summary.issue_count }}</h3>
                <p class="metric-label">发现问题</p>
              </div>
            </div>

            <div class="metric-item">
              <div class="metric-icon time">
                <el-icon><RefreshLeft /></el-icon>
              </div>
              <div class="metric-content">
                <h3 class="metric-value">{{ formatDuration(auditResults.summary.processing_time) }}</h3>
                <p class="metric-label">处理时间</p>
              </div>
            </div>

            <div class="metric-item">
              <div class="metric-icon confidence">
                <el-icon><SuccessFilled /></el-icon>
              </div>
              <div class="metric-content">
                <h3 class="metric-value">{{ (auditResults.summary.confidence_score * 100).toFixed(1) }}%</h3>
                <p class="metric-label">置信度</p>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 详细信息区域 -->
      <el-row :gutter="24">
        <!-- 左侧：合同信息 -->
        <el-col :lg="8" :md="24" :sm="24">
          <el-card class="contract-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><Document /></el-icon>
                <span class="header-title">合同信息</span>
              </div>
            </template>

            <div class="contract-content" v-if="auditResults.contract_info">
              <div class="contract-basic">
                <div class="info-row">
                  <span class="info-label">合同编号:</span>
                  <span class="info-value">{{ auditResults.contract_info.contract_number }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">买方:</span>
                  <span class="info-value">{{ auditResults.contract_info.buyer_name }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">卖方:</span>
                  <span class="info-value">{{ auditResults.contract_info.seller_name }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">合同金额:</span>
                  <span class="info-value">¥{{ formatCurrency(auditResults.contract_info.total_amount) }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">税率:</span>
                  <span class="info-value">{{ formatTaxRate(auditResults.contract_info.tax_rate) }}</span>
                </div>
                <div class="info-row" v-if="auditResults.contract_info.contract_date">
                  <span class="info-label">合同日期:</span>
                  <span class="info-value">{{ formatDate(auditResults.contract_info.contract_date) }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">置信度:</span>
                  <span class="info-value">{{ (auditResults.contract_info.confidence_score * 100).toFixed(1) }}%</span>
                </div>
              </div>

              <!-- 商品清单 -->
              <div class="contract-items" v-if="auditResults.contract_info.items">
                <h4 class="items-title">商品清单</h4>
                <el-table
                  :data="auditResults.contract_info.items"
                  size="small"
                  empty-text="合同未提取到商品清单，无法生成商品明细"
                >
                  <el-table-column prop="name" label="商品名称" />
                  <el-table-column prop="quantity" label="数量" width="80" align="center" />
                  <el-table-column prop="unit_price" label="单价" width="100" align="right">
                    <template #default="{ row }">
                      ¥{{ formatCurrency(row.unit_price) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="小计" width="100" align="right">
                    <template #default="{ row }">
                      {{ formatItemSubtotal(row) }}
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>

            <el-empty v-else description="暂无合同信息" />
          </el-card>
        </el-col>

        <!-- 中间：发票列表 -->
        <el-col :lg="8" :md="24" :sm="24">
          <el-card class="invoices-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><Document /></el-icon>
                <span class="header-title">发票列表</span>
                <div class="header-actions">
                  <el-tag type="info" size="small">
                    {{ auditResults.invoices?.length || 0 }} 张
                  </el-tag>
                </div>
              </div>
            </template>

            <div class="invoices-content">
              <div class="filter-section">
                <el-select
                  v-model="invoiceFilter"
                  placeholder="筛选状态"
                  size="small"
                  style="width: 120px"
                  @change="filterInvoices"
                >
                  <el-option label="全部" value="" />
                  <el-option label="正常" value="normal" />
                  <el-option label="重复" value="duplicate" />
                  <el-option label="错误" value="error" />
                </el-select>
              </div>

              <div class="invoice-list">
                <div
                  v-for="invoice in filteredInvoices"
                  :key="invoice.id"
                  class="invoice-item"
                  :class="{ 'is-duplicate': invoice.is_duplicate, 'has-error': invoice.status === 'error' }"
                >
                  <div class="invoice-header">
                    <div class="invoice-info">
                      <h4 class="invoice-number">{{ invoice.invoice_number }}</h4>
                      <el-tag
                        :type="getInvoiceStatusType(invoice.status)"
                        size="small"
                      >
                        {{ getInvoiceStatusText(invoice.status) }}
                      </el-tag>
                    </div>
                    <div class="invoice-amount">
                      <span class="amount-label">金额:</span>
                      <span class="amount-value">¥{{ formatCurrency(invoice.amount) }}</span>
                    </div>
                  </div>

                  <div class="invoice-details">
                    <div class="detail-row">
                      <span class="detail-label">税额:</span>
                      <span class="detail-value">¥{{ formatCurrency(invoice.tax_amount) }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">置信度:</span>
                      <span class="detail-value">{{ (invoice.confidence_score * 100).toFixed(1) }}%</span>
                    </div>
                    <div class="detail-row" v-if="invoice.is_duplicate && invoice.duplicate_of">
                      <span class="detail-label">重复发票:</span>
                      <el-tag type="warning" size="small">
                        与 {{ invoice.duplicate_of }} 重复
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>

              <el-empty v-if="filteredInvoices.length === 0" description="暂无发票数据" />
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：问题汇总 -->
        <el-col :lg="8" :md="24" :sm="24">
          <el-card class="issues-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><Warning /></el-icon>
                <span class="header-title">发现问题</span>
                <div class="header-actions">
                  <el-tag :type="getIssuesCountType()" size="small">
                    {{ auditResults.issues?.length || 0 }} 个
                  </el-tag>
                </div>
              </div>
            </template>

            <div class="issues-content">
              <div class="issues-filter">
                <el-select
                  v-model="issueFilter"
                  placeholder="筛选问题类型"
                  size="small"
                  style="width: 120px"
                  @change="filterIssues"
                >
                  <el-option label="全部" value="" />
                  <el-option label="严重" value="high" />
                  <el-option label="中等" value="medium" />
                  <el-option label="轻微" value="low" />
                </el-select>
              </div>

              <div class="issues-list">
                <div
                  v-for="issue in filteredIssues"
                  :key="issue.id"
                  class="issue-item"
                  :class="`severity-${issue.severity}`"
                >
                  <div class="issue-header">
                    <el-icon :class="getSeverityIcon(issue.severity)" class="severity-icon">
                      <component :is="getSeverityIcon(issue.severity)" />
                    </el-icon>
                    <div class="issue-info">
                      <h4 class="issue-title">{{ issue.title }}</h4>
                      <el-tag :type="getSeverityType(issue.severity)" size="small">
                        {{ getSeverityText(issue.severity) }}
                      </el-tag>
                    </div>
                  </div>

                  <div class="issue-description">
                    <p>{{ issue.description }}</p>
                  </div>

                  <div class="issue-recommendation">
                    <el-icon class="recommendation-icon"><InfoFilled /></el-icon>
                    <span class="recommendation-text">{{ issue.recommendation }}</span>
                  </div>
                </div>
              </div>

              <el-empty v-if="filteredIssues.length === 0" description="暂无发现问题" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 对比分析 -->
      <el-card class="comparison-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><DataAnalysis /></el-icon>
            <span class="header-title">合同-发票对比分析</span>
          </div>
        </template>

        <div class="comparison-content">
          <el-table
            :data="auditResults.comparisons"
            stripe
            empty-text="合同或发票缺少商品清单，暂无法生成逐项对比"
          >
            <el-table-column prop="product_name" label="商品名称" />
            <el-table-column prop="contract_quantity" label="合同数量" width="120" align="center" />
            <el-table-column prop="invoice_quantity" label="发票数量" width="120" align="center" />
            <el-table-column label="差异" width="100" align="center">
              <template #default="{ row }">
                <span :class="getDifferenceClass(row.difference)">
                  {{ row.difference > 0 ? '+' : '' }}{{ row.difference }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getComparisonStatusType(row.status)" size="small">
                  {{ getComparisonStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

      <!-- 操作区域 -->
      <div class="action-section">
        <el-card class="action-card" shadow="hover">
          <div class="action-content">
            <div class="action-buttons">
              <el-button
                type="primary"
                :icon="Download"
                @click="exportPDF"
                :loading="isExportingPDF"
              >
                导出PDF报告
              </el-button>

              <el-button
                type="success"
                @click="exportExcel"
                :loading="isExportingExcel"
              >
                导出Excel
              </el-button>

              <el-button
                type="info"
                @click="exportJSON"
                :loading="isExportingJSON"
              >
                导出JSON
              </el-button>

              <el-button
                :icon="Share"
                @click="generateShareLink"
                :loading="isGeneratingShare"
              >
                分享链接
              </el-button>

              <el-button
                :icon="RefreshLeft"
                @click="goBack"
              >
                返回上传
              </el-button>

              <el-button
                :icon="VideoPlay"
                type="warning"
                @click="reAudit"
                :loading="isReAuditing"
              >
                重新审计
              </el-button>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 分享链接对话框 -->
      <el-dialog
        v-model="shareDialogVisible"
        title="分享审计结果"
        width="500px"
        @close="closeShareDialog"
      >
        <div class="share-content">
          <div class="share-link-section">
            <p class="share-label">分享链接:</p>
            <div class="share-link-container">
              <el-input
                v-model="shareLink"
                readonly
                :suffix-icon="CopyDocument"
                @click="copyShareLink"
              />
            </div>
          </div>

          <div class="share-info">
            <el-alert
              title="分享信息"
              type="info"
              :closable="false"
              show-icon
            >
              <p>链接将在24小时后过期</p>
              <p v-if="sharePassword">访问密码: {{ sharePassword }}</p>
            </el-alert>
          </div>
        </div>

        <template #footer>
          <el-button @click="closeShareDialog">关闭</el-button>
        </template>
      </el-dialog>
    </div>

    <!-- 加载状态 -->
    <div v-else class="loading-container">
      <el-skeleton animated>
        <template #template>
          <div class="skeleton-content">
            <el-skeleton-item variant="text" style="width: 30%" />
            <el-skeleton-item variant="text" style="width: 60%; margin-top: 10px" />
            <el-skeleton-item variant="text" style="width: 40%; margin-top: 10px" />
          </div>
        </template>
      </el-skeleton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Warning,
  Download,
  Share,
  RefreshLeft,
  VideoPlay,
  CopyDocument,
  DataAnalysis,
  InfoFilled,
  Check,
  Close,
  SuccessFilled,
  InfoFilled as InfoIcon
} from '@element-plus/icons-vue'
import { useAuditStore } from '@/stores/audit'
import { apiService } from '@/services/api'

const router = useRouter()
const route = useRoute()
const auditStore = useAuditStore()

// 响应式数据
const auditId = ref(route.params.auditId as string)
const auditResults = ref<any>(null)
const loading = ref(true)

// 筛选器
const invoiceFilter = ref('')
const issueFilter = ref('')

// 操作状态
const isExportingPDF = ref(false)
const isExportingExcel = ref(false)
const isExportingJSON = ref(false)
const isGeneratingShare = ref(false)
const isReAuditing = ref(false)

// 分享相关
const shareDialogVisible = ref(false)
const shareLink = ref('')
const sharePassword = ref('')

// 计算属性
const filteredInvoices = computed(() => {
  if (!auditResults.value?.invoices) return []

  if (!invoiceFilter.value) return auditResults.value.invoices

  return auditResults.value.invoices.filter((invoice: any) =>
    invoice.status === invoiceFilter.value
  )
})

const filteredIssues = computed(() => {
  if (!auditResults.value?.issues) return []

  if (!issueFilter.value) return auditResults.value.issues

  return auditResults.value.issues.filter((issue: any) =>
    issue.severity === issueFilter.value
  )
})

// 方法定义
const normalizeAuditResults = (raw: any) => {
  const result = raw?.results || raw || {}
  const contractInfo = result.contract_info
    ? {
        ...result.contract_info,
        items: result.contract_info.items || result.contract_info.product_list || []
      }
    : null

  return {
    ...result,
    summary: {
      status: 'warning',
      contract_amount: 0,
      invoice_total: 0,
      coverage: 0,
      issue_count: 0,
      processing_time: 0,
      confidence_score: 0,
      ...(result.summary || {})
    },
    contract_info: contractInfo,
    invoices: (result.invoices || result.invoice_list || []).map((invoice: any, index: number) => ({
      id: invoice.id || invoice.invoice_number || invoice.source_file || `invoice-${index}`,
      amount: invoice.amount ?? invoice.total_amount ?? 0,
      tax_amount: invoice.tax_amount ?? 0,
      invoice_number: invoice.invoice_number || '未识别',
      status: invoice.status || 'normal',
      confidence_score: invoice.confidence_score ?? invoice.confidence ?? 0,
      ...invoice
    })),
    issues: (result.issues || []).map((issue: any, index: number) => ({
      id: issue.id || `${issue.type || 'issue'}-${index}`,
      recommendation: issue.recommendation || '建议人工复核',
      ...issue
    })),
    comparisons: result.comparisons || []
  }
}

const loadAuditResults = async () => {
  try {
    loading.value = true
    const results = await apiService.get(`/results/${auditId.value}`)
    auditResults.value = normalizeAuditResults(results)

    // 更新store中的结果
    auditStore.setCurrentResult(auditResults.value)
  } catch (error: any) {
    console.error('加载审计结果失败:', error)
    ElMessage.error('加载审计结果失败')
  } finally {
    loading.value = false
  }
}

const filterInvoices = () => {
  // 筛选逻辑已在计算属性中处理
}

const filterIssues = () => {
  // 筛选逻辑已在计算属性中处理
}

// 结论相关
const getConclusionIcon = (status: string) => {
  const iconMap: Record<string, any> = {
    'pass': Check,
    'fail': Close,
    'warning': Warning
  }
  return iconMap[status] || InfoFilled
}

const getConclusionTitle = (status: string) => {
  const titleMap: Record<string, string> = {
    'pass': '审计通过',
    'fail': '审计不通过',
    'warning': '需要人工复核'
  }
  return titleMap[status] || '审计结果'
}

const getConclusionSubtitle = (status: string) => {
  const subtitleMap: Record<string, string> = {
    'pass': '合同与发票匹配度良好，未发现重大问题',
    'fail': '发现严重问题，建议仔细核查',
    'warning': '发现一些问题，建议人工复核确认'
  }
  return subtitleMap[status] || '请查看详细结果'
}

// 发票状态
const getInvoiceStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'normal': 'success',
    'duplicate': 'warning',
    'error': 'danger'
  }
  return typeMap[status] || 'info'
}

const getInvoiceStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    'normal': '正常',
    'duplicate': '重复',
    'error': '错误'
  }
  return textMap[status] || status
}

// 问题严重程度
const getSeverityIcon = (severity: string) => {
  const iconMap: Record<string, any> = {
    'high': Close,
    'medium': Warning,
    'low': InfoFilled
  }
  return iconMap[severity] || InfoFilled
}

const getSeverityType = (severity: string) => {
  const typeMap: Record<string, string> = {
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return typeMap[severity] || 'info'
}

const getSeverityText = (severity: string) => {
  const textMap: Record<string, string> = {
    'high': '严重',
    'medium': '中等',
    'low': '轻微'
  }
  return textMap[severity] || severity
}

const getIssuesCountType = () => {
  if (!auditResults.value?.issues) return 'info'

  const hasHigh = auditResults.value.issues.some((issue: any) => issue.severity === 'high')
  const hasMedium = auditResults.value.issues.some((issue: any) => issue.severity === 'medium')

  if (hasHigh) return 'danger'
  if (hasMedium) return 'warning'
  return 'info'
}

// 对比分析
const getDifferenceClass = (difference: number) => {
  if (difference > 0) return 'text-danger'
  if (difference < 0) return 'text-warning'
  return 'text-success'
}

const getComparisonStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'match': 'success',
    'mismatch': 'warning',
    'partial': 'info'
  }
  return typeMap[status] || 'info'
}

const getComparisonStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    'match': '匹配',
    'mismatch': '不匹配',
    'partial': '部分匹配'
  }
  return textMap[status] || status
}

// 导出功能
const exportPDF = async () => {
  try {
    isExportingPDF.value = true
    await apiService.download(`/results/${auditId.value}/export/pdf`, `audit_report_${auditId.value}.pdf`)
    ElMessage.success('PDF报告导出成功')
  } catch (error: any) {
    ElMessage.error('导出PDF失败: ' + (error.message || '未知错误'))
  } finally {
    isExportingPDF.value = false
  }
}

const exportExcel = async () => {
  try {
    isExportingExcel.value = true
    await apiService.download(`/results/${auditId.value}/export/excel`, `audit_report_${auditId.value}.xlsx`)
    ElMessage.success('Excel报告导出成功')
  } catch (error: any) {
    ElMessage.error('导出Excel失败: ' + (error.message || '未知错误'))
  } finally {
    isExportingExcel.value = false
  }
}

const exportJSON = async () => {
  try {
    isExportingJSON.value = true
    const data = await apiService.get(`/results/${auditId.value}/export/json`)

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit_data_${auditId.value}.json`
    a.click()
    URL.revokeObjectURL(url)

    ElMessage.success('JSON数据导出成功')
  } catch (error: any) {
    ElMessage.error('导出JSON失败: ' + (error.message || '未知错误'))
  } finally {
    isExportingJSON.value = false
  }
}

// 分享功能
const generateShareLink = async () => {
  try {
    isGeneratingShare.value = true
    const shareInfo = await apiService.post(`/results/${auditId.value}/share`, {
      expire_hours: 24
    })

    shareLink.value = `${window.location.origin}${shareInfo.share_url}`
    sharePassword.value = shareInfo.password || ''
    shareDialogVisible.value = true

    ElMessage.success('分享链接生成成功')
  } catch (error: any) {
    ElMessage.error('生成分享链接失败: ' + (error.message || '未知错误'))
  } finally {
    isGeneratingShare.value = false
  }
}

const copyShareLink = () => {
  navigator.clipboard.writeText(shareLink.value)
  ElMessage.success('链接已复制到剪贴板')
}

const closeShareDialog = () => {
  shareDialogVisible.value = false
  shareLink.value = ''
  sharePassword.value = ''
}

// 其他操作
const reAudit = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重新进行审计吗？这将覆盖当前的审计结果。',
      '确认重新审计',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    isReAuditing.value = true
    await apiService.post('/audit/start', {
      task_id: auditId.value,
      audit_config: {
        enable_duplicate_detection: true,
        enable_amount_validation: true,
        enable_content_matching: true,
        confidence_threshold: 0.8,
        max_processing_time: 300
      }
    })

    ElMessage.success('重新审计已启动')
    router.push(`/audit/processing/${auditId.value}`)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('重新审计失败')
    }
  } finally {
    isReAuditing.value = false
  }
}

const goBack = () => {
  router.push('/audit/upload')
}

// 工具函数
const formatCurrency = (amount: number): string => {
  const value = Number(amount) || 0
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatTaxRate = (rate: number | string | null | undefined): string => {
  if (rate === null || rate === undefined || rate === '') {
    return '未识别'
  }
  const value = Number(rate) || 0
  return value > 1 ? `${value.toFixed(0)}%` : `${(value * 100).toFixed(0)}%`
}

const formatItemSubtotal = (row: any): string => {
  const explicitTotal = Number(row.total_amount ?? row.amount ?? row.subtotal)
  if (Number.isFinite(explicitTotal) && explicitTotal > 0) {
    return `¥${formatCurrency(explicitTotal)}`
  }

  const quantity = Number(row.quantity)
  const unitPrice = Number(row.unit_price)
  if (Number.isFinite(quantity) && Number.isFinite(unitPrice)) {
    return `¥${formatCurrency(quantity * unitPrice)}`
  }

  return '无法计算'
}

const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  if (hours > 0) {
    return `${hours}小时${minutes}分${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) {
    return dateString
  }
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 生命周期
onMounted(() => {
  loadAuditResults()
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
  padding: 24px;
}

.summary-header {
  margin-bottom: 32px;
}

.conclusion {
  display: flex;
  align-items: center;
  gap: 16px;
}

.conclusion-icon {
  font-size: 48px;
  padding: 16px;
  border-radius: 50%;
}

.conclusion-icon.conclusion-pass {
  background-color: #F0F9FF;
  color: #67C23A;
}

.conclusion-icon.conclusion-fail {
  background-color: #FEF0F0;
  color: #F56C6C;
}

.conclusion-icon.conclusion-warning {
  background-color: #FDF6EC;
  color: #E6A23C;
}

.conclusion-text {
  text-align: center;
}

.conclusion-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.conclusion-subtitle {
  font-size: 16px;
  color: #606266;
  margin: 0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin-bottom: 16px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background-color: #FAFAFA;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.metric-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.metric-icon.contract {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.metric-icon.invoice {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.metric-icon.coverage {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.metric-icon.issues {
  background: linear-gradient(135deg, #fa709a, #fee140);
}

.metric-icon.time {
  background: linear-gradient(135deg, #30cfd0, #330867);
}

.metric-icon.confidence {
  background: linear-gradient(135deg, #a8edea, #fed6e3);
}

.metric-content h3 {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.metric-content p {
  font-size: 14px;
  color: #606266;
  margin: 0;
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

.header-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.contract-card,
.invoices-card,
.issues-card {
  margin-bottom: 24px;
}

.contract-content,
.invoices-content,
.issues-content {
  margin-top: 16px;
}

.contract-basic {
  margin-bottom: 20px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #F0F0F0;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #303133;
  font-weight: 600;
}

.items-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.filter-section {
  margin-bottom: 16px;
}

.invoice-list {
  max-height: 400px;
  overflow-y: auto;
}

.invoice-item {
  padding: 16px;
  border: 1px solid #EBEEF5;
  border-radius: 8px;
  margin-bottom: 12px;
  background-color: #FAFAFA;
  transition: all 0.3s ease;
}

.invoice-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.invoice-item.is-duplicate {
  border-color: #E6A23C;
  background-color: #FDF6EC;
}

.invoice-item.has-error {
  border-color: #F56C6C;
  background-color: #FEF0F0;
}

.invoice-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.invoice-info {
  flex: 1;
}

.invoice-number {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.invoice-amount {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.amount-label {
  color: #606266;
}

.amount-value {
  color: #303133;
  font-weight: 600;
}

.invoice-details {
  font-size: 13px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.detail-label {
  color: #606266;
  min-width: 60px;
}

.detail-value {
  color: #303133;
}

.issues-list {
  max-height: 400px;
  overflow-y: auto;
}

.issue-item {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  background-color: #FAFAFA;
  border-left: 4px solid #E4E7ED;
}

.issue-item.severity-high {
  border-left-color: #F56C6C;
  background-color: #FEF0F0;
}

.issue-item.severity-medium {
  border-left-color: #E6A23C;
  background-color: #FDF6EC;
}

.issue-item.severity-low {
  border-left-color: #409EFF;
  background-color: #ECF5FF;
}

.issue-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.severity-icon {
  font-size: 16px;
  margin-right: 8px;
}

.severity-icon.high {
  color: #F56C6C;
}

.severity-icon.medium {
  color: #E6A23C;
}

.severity-icon.low {
  color: #409EFF;
}

.issue-info {
  flex: 1;
}

.issue-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.issue-description {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 12px;
}

.issue-recommendation {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  background-color: #F0F9FF;
  border-radius: 6px;
}

.recommendation-icon {
  color: #409EFF;
  font-size: 14px;
  margin-top: 2px;
}

.recommendation-text {
  font-size: 13px;
  color: #303133;
  line-height: 1.4;
}

.comparison-card {
  margin-bottom: 24px;
}

.comparison-content {
  margin-top: 16px;
}

.text-danger {
  color: #F56C6C;
  font-weight: 600;
}

.text-warning {
  color: #E6A23C;
  font-weight: 600;
}

.text-success {
  color: #67C23A;
  font-weight: 600;
}

.action-card {
  margin-bottom: 24px;
}

.action-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.loading-container {
  padding: 24px;
}

.skeleton-content {
  padding: 24px;
}

.share-content {
  padding: 16px 0;
}

.share-link-section {
  margin-bottom: 16px;
}

.share-label {
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
  font-weight: 500;
}

.share-link-container {
  display: flex;
  gap: 8px;
}

.share-info {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .results-page {
    padding: 16px;
  }

  .page-title {
    font-size: 24px;
  }

  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .conclusion {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }

  .action-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .action-buttons {
    flex-direction: column;
  }

  .share-link-container {
    flex-direction: column;
  }
}
</style>
