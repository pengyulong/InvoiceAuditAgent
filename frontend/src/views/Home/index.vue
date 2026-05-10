<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-kicker">智能合同发票审计系统</div>
        <h1 class="hero-title">AI驱动的智能审计解决方案</h1>
        <p class="hero-subtitle">
          自动识别发票信息，批量处理文件，并完成合同与发票的匹配审计。
        </p>
      </div>
    </section>

    <!-- 双入口卡片 -->
    <section class="entry-section">
      <div class="section-header">
        <h2 class="section-title">选择服务模式</h2>
        <p class="section-subtitle">根据您的需求选择合适的处理方式</p>
      </div>

      <el-row :gutter="32" class="entry-cards">
        <!-- 发票识别 -->
        <el-col :lg="12" :md="24" :sm="24">
          <el-card class="entry-card invoice-card" shadow="hover">
            <div class="entry-content">
              <div class="entry-icon invoice-icon">🧾</div>
              <h3 class="entry-title">发票识别</h3>
              <p class="entry-description">
                快速提取发票关键信息，支持批量识别和Excel导出
              </p>
              <ul class="entry-features">
                <li>支持 PDF / JPG / PNG 多格式发票上传</li>
                <li>批量识别，自动提取发票号码、金额、税率等</li>
                <li>识别结果支持导出为 Excel / JSON 格式</li>
                <li>支持增值税发票、普通发票等多种类型</li>
              </ul>
              <el-button
                type="primary"
                size="large"
                class="entry-button"
                @click="goToInvoice"
              >
                <el-icon><UploadFilled /></el-icon>
                开始发票识别
              </el-button>
            </div>
          </el-card>
        </el-col>

        <!-- 合同审计 -->
        <el-col :lg="12" :md="24" :sm="24">
          <el-card class="entry-card audit-card" shadow="hover">
            <div class="entry-content">
              <div class="entry-icon audit-icon">📋</div>
              <h3 class="entry-title">合同审计</h3>
              <p class="entry-description">
                智能比对合同与发票，自动检测差异和风险
              </p>
              <ul class="entry-features">
                <li>上传合同 + 发票 ZIP 压缩包，自动分类解析</li>
                <li>AI 智能比对金额、税率、商品清单等关键信息</li>
                <li>自动检测重复发票、金额不符等异常问题</li>
                <li>生成详细审计报告，支持 PDF / Excel 导出</li>
              </ul>
              <el-button
                type="success"
                size="large"
                class="entry-button"
                @click="goToAudit"
              >
                <el-icon><Document /></el-icon>
                开始合同审计
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="section-header">
        <h2 class="section-title">核心功能</h2>
        <p class="section-subtitle">为企业提供专业的智能审计服务</p>
      </div>

      <el-row :gutter="24" class="features-grid">
        <el-col :lg="8" :md="12" :sm="24" v-for="feature in features" :key="feature.id">
          <el-card class="feature-card" shadow="hover">
            <div class="feature-icon">
              <span :style="`font-size: 48px; color: ${feature.color}`">
                {{ feature.icon }}
              </span>
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-description">{{ feature.description }}</p>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <!-- Statistics Section -->
    <section class="stats-section">
      <div class="section-header">
        <h2 class="section-title">系统统计</h2>
        <p class="section-subtitle">实时展示系统运行数据</p>
      </div>

      <el-row :gutter="24" class="stats-grid">
        <el-col :lg="6" :md="12" :sm="24" v-for="stat in statistics" :key="stat.key">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon">
                <span :style="`font-size: 32px; color: ${stat.color}`">
                  {{ stat.icon }}
                </span>
              </div>
              <div class="stat-info">
                <h3 class="stat-value">{{ stat.value }}</h3>
                <p class="stat-label">{{ stat.label }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { UploadFilled, Document } from '@element-plus/icons-vue'

const router = useRouter()

const features = ref([
  {
    id: 1,
    icon: '🤖',
    title: '自动化审计',
    description: '替代人工审核，提高审计效率90%以上',
    color: '#409EFF'
  },
  {
    id: 2,
    icon: '📊',
    title: '智能分析',
    description: '利用AI模型理解合同和发票图像内容',
    color: '#67C23A'
  },
  {
    id: 3,
    icon: '🛡️',
    title: '风险识别',
    description: '自动发现重复发票、金额不符等异常问题',
    color: '#E6A23C'
  }
])

const statistics = ref([
  {
    key: 'totalAudits',
    icon: '📄',
    label: '总审计次数',
    value: '1,234',
    color: '#409EFF'
  },
  {
    key: 'successRate',
    icon: '📈',
    label: '成功率',
    value: '98.5%',
    color: '#67C23A'
  },
  {
    key: 'processingTime',
    icon: '🤖',
    label: '平均处理时间',
    value: '2.5分钟',
    color: '#E6A23C'
  },
  {
    key: 'issuesFound',
    icon: '🛡️',
    label: '发现问题',
    value: '456',
    color: '#F56C6C'
  }
])

const goToInvoice = () => {
  router.push('/invoice/upload')
}

const goToAudit = () => {
  router.push('/audit/upload')
}

onMounted(() => {
  // 可以在这里加载统计数据
})
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8fafc 0%, #eef4fb 100%);
}

.hero-section {
  padding: 32px 24px 12px;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 8px 4px 0;
  text-align: center;
}

.hero-kicker {
  display: inline-flex;
  align-items: center;
  margin-bottom: 14px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #eef4ff;
  color: #2563eb;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0;
}

.hero-title {
  font-size: 40px;
  font-weight: 700;
  margin-bottom: 24px;
  line-height: 1.2;
  color: #172033;
}

.hero-subtitle {
  font-size: 20px;
  line-height: 1.6;
  color: #5b6575;
  max-width: 680px;
  margin: 0 auto;
}

/* 双入口卡片 */
.entry-section {
  padding: 56px 0 0;
}

.entry-cards {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 20px;
}

.entry-card {
  margin-bottom: 24px;
  border-radius: 8px;
  border: 1px solid #e6edf6;
  transition: all 0.3s ease;
  height: 100%;
  background: #ffffff;
}

.entry-card:hover {
  transform: translateY(-8px);
  border-color: #d7e2ef;
}

.invoice-card {
  border-top: 4px solid #409EFF;
}

.invoice-card:hover {
  box-shadow: 0 20px 40px rgba(64, 158, 255, 0.15);
}

.audit-card {
  border-top: 4px solid #67C23A;
}

.audit-card:hover {
  box-shadow: 0 20px 40px rgba(103, 194, 58, 0.15);
}

.entry-content {
  text-align: center;
  padding: 28px 24px;
}

.entry-icon {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  margin: 0 auto 24px;
}

.invoice-icon {
  background: #eef4ff;
}

.audit-icon {
  background: #eefaf4;
}

.entry-title {
  font-size: 28px;
  font-weight: 700;
  color: #172033;
  margin-bottom: 12px;
}

.entry-description {
  font-size: 16px;
  color: #606266;
  margin-bottom: 24px;
  line-height: 1.6;
}

.entry-features {
  text-align: left;
  margin: 0 auto 32px;
  padding: 0;
  list-style: none;
  max-width: 360px;
}

.entry-features li {
  position: relative;
  padding: 8px 0 8px 28px;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.entry-features li::before {
  content: '✓';
  position: absolute;
  left: 0;
  top: 8px;
  color: #67C23A;
  font-weight: 700;
}

.entry-button {
  min-width: 200px;
  height: 48px;
  font-size: 16px;
  border-radius: 8px;
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-title {
  font-size: 36px;
  font-weight: 600;
  color: #172033;
  margin-bottom: 16px;
}

.section-subtitle {
  font-size: 18px;
  color: #606266;
  line-height: 1.6;
}

.features-section,
.stats-section {
  padding: 80px 0;
}

.features-grid,
.stats-grid {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.feature-card {
  height: 280px;
  text-align: center;
  transition: all 0.3s ease;
  border: 1px solid #e6edf6;
  border-radius: 8px;
  background: #fff;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
}

.feature-icon {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.feature-title {
  font-size: 24px;
  font-weight: 600;
  color: #172033;
  margin-bottom: 16px;
}

.feature-description {
  font-size: 16px;
  color: #606266;
  line-height: 1.6;
}

.stats-section {
  background: transparent;
}

.stat-card {
  height: 140px;
  display: flex;
  align-items: center;
  border-radius: 8px;
  border: 1px solid #e6edf6;
  background: #fff;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
  text-align: left;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #172033;
  margin-bottom: 4px;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

@media (max-width: 768px) {
  .hero-section {
    padding: 16px 16px 8px;
  }

  .hero-title {
    font-size: 32px;
  }

  .hero-subtitle {
    font-size: 18px;
  }

  .entry-content {
    padding: 24px 16px;
  }

  .entry-title {
    font-size: 24px;
  }

  .section-title {
    font-size: 28px;
  }

  .feature-card {
    height: 240px;
    margin-bottom: 16px;
  }

  .entry-button {
    min-width: 160px;
  }
}
</style>
