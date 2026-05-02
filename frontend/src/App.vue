<template>
  <div id="app">
    <el-container>
      <!-- Header -->
      <el-header v-if="!isLoginPage" class="app-header">
        <div class="header-content">
          <div class="logo">
            <span class="logo-icon">📄</span>
            <span class="logo-text">智能合同发票审计系统</span>
          </div>
          <div class="header-actions">
            <el-badge :value="notificationCount" class="notification-badge">
              <el-button circle>🔔</el-button>
            </el-badge>
            <el-dropdown>
              <el-button circle>👤</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item disabled>{{ username || 'admin' }}</el-dropdown-item>
                  <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <!-- Main Content -->
      <el-main :class="isLoginPage ? 'login-main' : 'app-main'">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authStorage } from '@/services/api'
// import { Document, Bell, User } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const notificationCount = ref(0)
const isLoginPage = computed(() => route.path === '/login')
const username = computed(() => authStorage.getUsername())

const logout = () => {
  authStorage.clearSession()
  router.replace('/login')
}
</script>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0;
  height: 64px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: 600;
}

.logo-icon {
  font-size: 28px;
  margin-right: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.notification-badge {
  margin-right: 8px;
}

.app-main {
  min-height: calc(100vh - 64px);
  background-color: #f5f7fa;
  padding: 20px;
}

.login-main {
  min-height: 100vh;
  padding: 0;
}
</style>
