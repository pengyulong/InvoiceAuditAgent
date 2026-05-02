import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home/index.vue'
import { authStorage } from '@/services/api'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login/index.vue'),
      meta: {
        title: '登录',
        public: true
      }
    },
    {
      path: '/',
      name: 'Home',
      component: Home,
      meta: {
        title: '首页'
      }
    },
    {
      path: '/audit',
      name: 'Audit',
      redirect: '/audit/upload',
      meta: {
        title: '审计管理'
      },
      children: [
        {
          path: 'upload',
          name: 'FileUpload',
          component: () => import('@/views/Audit/Upload.vue'),
          meta: {
            title: '文件上传'
          }
        },
        {
          path: 'processing/:taskId?',
          name: 'AuditProcessing',
          component: () => import('@/views/Audit/Processing.vue'),
          meta: {
            title: '审计进度'
          }
        }
      ]
    },
    {
      path: '/invoice',
      name: 'Invoice',
      redirect: '/invoice/upload',
      meta: {
        title: '发票识别'
      },
      children: [
        {
          path: 'upload',
          name: 'InvoiceUpload',
          component: () => import('@/views/Invoice/Upload.vue'),
          meta: {
            title: '发票上传'
          }
        },
        {
          path: 'processing/:taskId?',
          name: 'InvoiceProcessing',
          component: () => import('@/views/Invoice/Processing.vue'),
          meta: {
            title: '识别进度'
          }
        },
        {
          path: 'results/:taskId',
          name: 'InvoiceResults',
          component: () => import('@/views/Invoice/Results.vue'),
          meta: {
            title: '识别结果'
          }
        }
      ]
    },
    {
      path: '/results/:auditId?',
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
        title: '页面未找到'
      }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 智能合同发票审计系统`
  }

  if (!to.meta?.public && !authStorage.isAuthenticated()) {
    next({
      path: '/login',
      query: {
        redirect: to.fullPath
      }
    })
    return
  }

  if (to.path === '/login' && authStorage.isAuthenticated()) {
    next((to.query.redirect as string) || '/audit/upload')
    return
  }

  next()
})

export default router
