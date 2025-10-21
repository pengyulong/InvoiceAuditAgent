<template>
  <div class="home-container">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-content">
        <div class="logo">
          <el-icon class="logo-icon"><Document /></el-icon>
          <h1 class="logo-text">智能合同发票审计系统</h1>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="startAudit">
            <el-icon><Upload /></el-icon>
            开始审计
          </el-button>
        </div>
      </div>
    </header>

    <!-- 主要内容 -->
    <main class="main-content">
      <!-- Hero区域 -->
      <section class="hero-section">
        <div class="hero-content">
          <h2 class="hero-title">基于AI的智能审计解决方案</h2>
          <p class="hero-description">
            通过多模态大模型和LLM技术，自动化审计采购合同与发票的匹配性、合规性和准确性
          </p>
          <div class="hero-actions">
            <el-button size="large" type="primary" @click="startAudit">
              <el-icon><Plus /></el-icon>
              创建审计任务
            </el-button>
            <el-button size="large" @click="viewDemo">
              <el-icon><VideoPlay /></el-icon>
              观看演示
            </el-button>
          </div>
        </div>
        <div class="hero-image">
          <img src="/src/assets/images/hero-illustration.svg" alt="智能审计" />
        </div>
      </section>

      <!-- 特性介绍 -->
      <section class="features-section">
        <div class="container">
          <h3 class="section-title">核心功能特性</h3>
          <div class="features-grid">
            <div class="feature-card">
              <div class="feature-icon">
                <el-icon size="48"><View /></el-icon>
              </div>
              <h4 class="feature-title">智能识别</h4>
              <p class="feature-description">
                使用先进的多模态AI技术，准确识别合同和发票中的关键信息
              </p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">
                <el-icon size="48"><Connection /></el-icon>
              </div>
              <h4 class="feature-title">交叉验证</h4>
              <p class="feature-description">
                自动匹配合同与发票信息，发现不一致之处和潜在风险
              </p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">
                <el-icon size="48"><Warning /></el-icon>
              </div>
              <h4 class="feature-title">风险检测</h4>
              <p class="feature-description">
                智能识别重复发票、金额异常等风险问题，提供专业建议
              </p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">
                <el-icon size="48"><Document /></el-icon>
              </div>
              <h4 class="feature-title">报告生成</h4>
              <p class="feature-description">
                自动生成详细的审计报告，支持多种格式导出和分享
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- 统计数据 -->
      <section class="stats-section">
        <div class="container">
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-number">90%+</div>
              <div class="stat-label">审计效率提升</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">95%+</div>
              <div class="stat-label">识别准确率</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">60秒</div>
              <div class="stat-label">平均审计时间</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">24/7</div>
              <div class="stat-label">全天候服务</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 使用流程 -->
      <section class="workflow-section">
        <div class="container">
          <h3 class="section-title">使用流程</h3>
          <div class="workflow-steps">
            <div class="step-item">
              <div class="step-number">1</div>
              <div class="step-content">
                <h4 class="step-title">上传文件</h4>
                <p class="step-description">上传包含合同和发票的ZIP文件</p>
              </div>
            </div>
            <div class="step-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
            <div class="step-item">
              <div class="step-number">2</div>
              <div class="step-content">
                <h4 class="step-title">AI分析</h4>
                <p class="step-description">系统自动分析文件内容并提取关键信息</p>
              </div>
            </div>
            <div class="step-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
            <div class="step-item">
              <div class="step-number">3</div>
              <div class="step-content">
                <h4 class="step-title">交叉验证</h4>
                <p class="step-description">对比合同与发票信息，检测异常情况</p>
              </div>
            </div>
            <div class="step-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
            <div class="step-item">
              <div class="step-number">4</div>
              <div class="step-content">
                <h4 class="step-title">生成报告</h4>
                <p class="step-description">获得详细的审计报告和专业建议</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="container">
        <div class="footer-content">
          <div class="footer-section">
            <h5>智能合同发票审计系统</h5>
            <p>基于AI的专业审计解决方案</p>
          </div>
          <div class="footer-section">
            <h5>技术支持</h5>
            <p>多模态大模型 | LLM技术 | 智能分析</p>
          </div>
          <div class="footer-section">
            <h5>联系我们</h5>
            <p>获取技术支持和产品咨询</p>
          </div>
        </div>
        <div class="footer-bottom">
          <p>&copy; 2024 智能合同发票审计系统. 保留所有权利.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const startAudit = () => {
  router.push('/audit/upload')
}

const viewDemo = () => {
  // 这里可以添加演示视频或示例链接
  ElMessage.info('演示功能开发中，敬请期待！')
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-icon {
  font-size: 2rem;
  color: white;
}

.logo-text {
  color: white;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.main-content {
  padding: 2rem;
}

.hero-section {
  max-width: 1200px;
  margin: 0 auto 4rem;
  padding: 4rem 2rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
}

.hero-content h2 {
  color: white;
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  line-height: 1.2;
}

.hero-description {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.25rem;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 1rem;
}

.hero-image {
  display: flex;
  justify-content: center;
  align-items: center;
}

.hero-image img {
  max-width: 100%;
  height: auto;
}

.features-section {
  background: white;
  border-radius: 1rem;
  padding: 4rem 2rem;
  margin-bottom: 4rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  text-align: center;
  font-size: 2.5rem;
  font-weight: 600;
  margin-bottom: 3rem;
  color: #1f2937;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
}

.feature-card {
  text-align: center;
  padding: 2rem;
  border-radius: 0.75rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  color: #6366f1;
  margin-bottom: 1.5rem;
}

.feature-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #1f2937;
}

.feature-description {
  color: #6b7280;
  line-height: 1.6;
}

.stats-section {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  padding: 3rem 2rem;
  margin-bottom: 4rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 3rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.1rem;
}

.workflow-section {
  background: white;
  border-radius: 1rem;
  padding: 4rem 2rem;
  margin-bottom: 4rem;
}

.workflow-steps {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 200px;
}

.step-number {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #6366f1;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.step-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #1f2937;
}

.step-description {
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.4;
}

.step-arrow {
  color: #6b7280;
  font-size: 1.5rem;
}

.footer {
  background: rgba(0, 0, 0, 0.2);
  color: white;
  padding: 2rem;
}

.footer-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.footer-section h5 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.footer-section p {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.5;
}

.footer-bottom {
  text-align: center;
  padding-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.6);
}

@media (max-width: 768px) {
  .hero-section {
    grid-template-columns: 1fr;
    text-align: center;
    gap: 2rem;
  }

  .hero-content h2 {
    font-size: 2rem;
  }

  .workflow-steps {
    flex-direction: column;
  }

  .step-arrow {
    transform: rotate(90deg);
  }
}
</style>