import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 状态
  const loading = ref(false)
  const theme = ref<'light' | 'dark'>('light')
  const sidebarCollapsed = ref(false)
  const notifications = ref<Array<{
    id: string
    type: 'info' | 'success' | 'warning' | 'error'
    title: string
    message: string
    timestamp: number
  }>>([])

  // 计算属性
  const notificationCount = computed(() => notifications.value.length)

  // 方法
  const setLoading = (value: boolean) => {
    loading.value = value
  }

  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const addNotification = (notification: {
    type: 'info' | 'success' | 'warning' | 'error'
    title: string
    message: string
  }) => {
    const id = Date.now().toString()
    notifications.value.push({
      id,
      ...notification,
      timestamp: Date.now()
    })
  }

  const removeNotification = (id: string) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  const clearNotifications = () => {
    notifications.value = []
  }

  return {
    // 状态
    loading,
    theme,
    sidebarCollapsed,
    notifications,
    // 计算属性
    notificationCount,
    // 方法
    setLoading,
    toggleTheme,
    toggleSidebar,
    addNotification,
    removeNotification,
    clearNotifications
  }
})