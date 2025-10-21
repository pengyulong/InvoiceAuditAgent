import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home/index.vue'),
    meta: {
      title: '智能合同发票审计系统'
    }
  },
  {
    path: '/audit',
    name: 'Audit',
    component: () => import('@/views/Audit/index.vue'),
    meta: {
      title: '审计工作台'
    }
  },
  {
    path: '/audit/upload',
    name: 'FileUpload',
    component: () => import('@/views/Audit/Upload.vue'),
    meta: {
      title: '文件上传'
    }
  },
  {
    path: '/audit/processing/:taskId',
    name: 'AuditProcessing',
    component: () => import('@/views/Audit/Processing.vue'),
    meta: {
      title: '审计处理中'
    }
  },
  {
    path: '/results/:auditId',
    name: 'Results',
    component: () => import('@/views/Results/index.vue'),
    meta: {
      title: '审计结果'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound/index.vue'),
    meta: {
      title: '页面不存在'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = to.meta.title as string
  }
  next()
})

export default router