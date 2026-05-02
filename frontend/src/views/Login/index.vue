<template>
  <div class="login-page">
    <section class="login-shell">
      <div class="brand-panel">
        <div class="brand-mark">票</div>
        <h1>智能合同发票审计系统</h1>
        <p>登录后上传合同与发票文件，执行审计并查看结果。</p>
      </div>

      <el-card class="login-card" shadow="never">
        <template #header>
          <div class="card-header">
            <h2>账号登录</h2>
            <span>仅授权用户可访问系统</span>
          </div>
        </template>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model.trim="form.username"
              placeholder="请输入用户名"
              autocomplete="username"
              size="large"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              autocomplete="current-password"
              show-password
              size="large"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-button
            class="login-button"
            type="primary"
            size="large"
            :loading="isSubmitting"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form>
      </el-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { apiService, authStorage } from '@/services/api'

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const isSubmitting = ref(false)

const form = reactive({
  username: 'admin',
  password: ''
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  try {
    isSubmitting.value = true
    const result = await apiService.post('/auth/login', {
      username: form.username,
      password: form.password
    })
    authStorage.setSession(result.access_token, result.username)
    ElMessage.success('登录成功')
    router.replace((route.query.redirect as string) || '/audit/upload')
  } catch (error) {
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px;
  background:
    linear-gradient(135deg, rgba(30, 64, 175, 0.92), rgba(22, 101, 52, 0.86)),
    url('https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=1600&q=80') center / cover;
}

.login-shell {
  width: min(960px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 32px;
  align-items: center;
}

.brand-panel {
  color: #fff;
}

.brand-mark {
  width: 56px;
  height: 56px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.42);
  border-radius: 8px;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
}

.brand-panel h1 {
  font-size: 42px;
  line-height: 1.18;
  margin: 0 0 16px;
  font-weight: 700;
}

.brand-panel p {
  max-width: 480px;
  font-size: 17px;
  line-height: 1.7;
  margin: 0;
  color: rgba(255, 255, 255, 0.84);
}

.login-card {
  border: 0;
  border-radius: 8px;
}

.card-header h2 {
  margin: 0 0 6px;
  font-size: 22px;
}

.card-header span {
  color: #606266;
  font-size: 14px;
}

.login-button {
  width: 100%;
  margin-top: 8px;
}

@media (max-width: 760px) {
  .login-page {
    padding: 20px;
  }

  .login-shell {
    grid-template-columns: 1fr;
  }

  .brand-panel h1 {
    font-size: 30px;
  }
}
</style>
