<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">AI驱动的智能审计解决方案</h1>
        <p class="hero-subtitle">
          通过先进的多模态大模型技术，自动化审计采购合同与发票的匹配性、合规性和准确性
        </p>
        <el-button
          type="primary"
          size="large"
          class="cta-button"
          @click="startAudit"
        >
          <span class="mr-2">▶️</span>
          开始审计
        </el-button>
      </div>
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
// import { Play, Robot, DataAnalysis, Shield, Document, TrendCharts } from '@element-plus/icons-vue'
import { useAuditStore } from '@/stores/audit'

const router = useRouter()
const auditStore = useAuditStore()

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
    description: '利用多模态大模型理解合同和发票图像内容',
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

const startAudit = () => {
  router.push('/audit/upload')
}

onMounted(() => {
  // 可以在这里加载统计数据
})
</script>

<style scoped>
.home {
  min-height: 100vh;
}

.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 120px 0;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
  opacity: 0.3;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 20px;
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 24px;
  line-height: 1.2;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.hero-subtitle {
  font-size: 20px;
  line-height: 1.6;
  margin-bottom: 40px;
  opacity: 0.9;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.cta-button {
  font-size: 18px;
  padding: 16px 32px;
  height: auto;
  border-radius: 50px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.3);
}

.features-section,
.stats-section {
  padding: 80px 0;
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-title {
  font-size: 36px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.section-subtitle {
  font-size: 18px;
  color: #606266;
  line-height: 1.6;
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
  border: none;
  border-radius: 16px;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.feature-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.feature-description {
  font-size: 16px;
  color: #606266;
  line-height: 1.6;
}

.stats-section {
  background-color: #f8f9fa;
}

.stat-card {
  height: 140px;
  display: flex;
  align-items: center;
  border-radius: 12px;
  border: none;
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
  color: #303133;
  margin-bottom: 4px;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 32px;
  }

  .hero-subtitle {
    font-size: 18px;
  }

  .section-title {
    font-size: 28px;
  }

  .feature-card {
    height: 240px;
    margin-bottom: 16px;
  }
}
</style>