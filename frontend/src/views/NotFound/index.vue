<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-illustration">
        <el-icon class="error-icon"><WarningFilled /></el-icon>
        <div class="error-code">404</div>
      </div>

      <div class="error-info">
        <h1>页面不存在</h1>
        <p>抱歉，您访问的页面不存在或已被移除</p>

        <div class="action-buttons">
          <el-button type="primary" @click="goHome">
            <el-icon><House /></el-icon>
            返回首页
          </el-button>
          <el-button @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回上页
          </el-button>
        </div>

        <div class="help-links">
          <h3>您可能想要：</h3>
          <ul>
            <li><router-link to="/audit">审计工作台</router-link></li>
            <li><router-link to="/audit/upload">上传文件</router-link></li>
            <li><router-link to="/results">查看结果</router-link></li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.not-found-content {
  text-align: center;
  background: white;
  border-radius: 16px;
  padding: 3rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  width: 100%;
}

.error-illustration {
  margin-bottom: 2rem;
  position: relative;
}

.error-icon {
  font-size: 120px;
  color: #fbbf24;
  opacity: 0.8;
}

.error-code {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 48px;
  font-weight: 700;
  color: #1f2937;
  opacity: 0.9;
}

.error-info h1 {
  font-size: 2rem;
  color: #1f2937;
  margin-bottom: 1rem;
  font-weight: 600;
}

.error-info p {
  color: #6b7280;
  font-size: 1rem;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 3rem;
}

.help-links h3 {
  font-size: 1.1rem;
  color: #1f2937;
  margin-bottom: 1rem;
  font-weight: 600;
}

.help-links ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.help-links li {
  margin-bottom: 0.5rem;
}

.help-links a {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.help-links a:hover {
  color: #2563eb;
  text-decoration: underline;
}

@media (max-width: 768px) {
  .not-found-container {
    padding: 1rem;
  }

  .not-found-content {
    padding: 2rem 1.5rem;
  }

  .error-icon {
    font-size: 80px;
  }

  .error-code {
    font-size: 36px;
  }

  .error-info h1 {
    font-size: 1.5rem;
  }

  .action-buttons {
    flex-direction: column;
    align-items: center;
  }

  .action-buttons .el-button {
    width: 200px;
  }
}
</style>