import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/stores/app'
import type { ApiResponse } from '@/types'

const TOKEN_KEY = 'invoice_audit_access_token'
const USER_KEY = 'invoice_audit_username'

export const authStorage = {
  getToken(): string {
    return localStorage.getItem(TOKEN_KEY) || ''
  },
  getUsername(): string {
    return localStorage.getItem(USER_KEY) || ''
  },
  setSession(token: string, username: string) {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, username)
  },
  clearSession() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },
  isAuthenticated(): boolean {
    return Boolean(this.getToken())
  }
}

class ApiService {
  private instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  private getErrorMessage(error: any): string {
    if (error?.code === 'ECONNABORTED') {
      return '请求超时，请稍后重试'
    }

    if (!error?.response) {
      return '网络连接失败，请检查网络设置'
    }

    const { status, data } = error.response
    const serverMessage = typeof data === 'string'
      ? ''
      : data?.message || data?.detail || ''

    switch (status) {
      case 400:
        return serverMessage || '请求参数错误'
      case 401:
        return '未授权，请重新登录'
      case 403:
        return '拒绝访问'
      case 404:
        return '请求的资源不存在'
      case 413:
        return serverMessage || '文件过大，请选择更小的文件'
      case 500:
        return serverMessage || '服务器内部错误'
      default:
        return serverMessage || `请求失败 (${status})`
    }
  }

  private setupInterceptors() {
    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        const appStore = useAppStore()
        if ((config as AxiosRequestConfig & { loading?: boolean }).loading !== false) {
          appStore.setLoading(true)
        }
        const token = authStorage.getToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        const appStore = useAppStore()
        appStore.setLoading(false)
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        const appStore = useAppStore()
        appStore.setLoading(false)

        const { data } = response

        // 检查响应格式 - 支持两种格式：
        // 1. {code: 200, data: {...}} 标准格式
        // 2. 直接返回数据格式（文件上传等接口）
        if (data.code !== undefined && data.code !== 200) {
          ElMessage.error(data.message || '请求失败')
          return Promise.reject(new Error(data.message))
        }

        return response
      },
      (error) => {
        const appStore = useAppStore()
        appStore.setLoading(false)

        const message = this.getErrorMessage(error)
        if (error?.response?.status === 401) {
          authStorage.clearSession()
          if (window.location.pathname !== '/login') {
            window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}`
          }
        }

        ElMessage.error(message)
        return Promise.reject(error)
      }
    )
  }

  // GET 请求
  async get<T = any>(url: string, params?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get(url, { params, ...config })
    // 支持两种响应格式：{code: 200, data: {...}} 或直接返回数据
    return response.data.data || response.data
  }

  // POST 请求
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post(url, data, config)
    // 支持两种响应格式：{code: 200, data: {...}} 或直接返回数据
    return response.data.data || response.data
  }

  // PUT 请求
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put(url, data, config)
    // 支持两种响应格式：{code: 200, data: {...}} 或直接返回数据
    return response.data.data || response.data
  }

  // DELETE 请求
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete(url, config)
    // 支持两种响应格式：{code: 200, data: {...}} 或直接返回数据
    return response.data.data || response.data
  }

  // 文件上传
  async upload<T = any>(
    url: string,
    formData: FormData,
    onProgress?: (progress: number) => void,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.instance.post(url, formData, {
      timeout: config?.timeout ?? 10 * 60 * 1000,
      ...config,
      headers: {
        ...(config?.headers || {}),
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
    // 文件上传接口直接返回数据，没有.data字段
    return response.data
  }

  // 下载文件
  async download(url: string, filename?: string): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob'
    })

    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }
}

export const apiService = new ApiService()
export default apiService
