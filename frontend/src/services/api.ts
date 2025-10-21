import axios from 'axios'
import type { ApiResponse } from '@/types'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000, // 60秒超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    console.log('API请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('API响应:', response.status, response.data)

    // 检查业务状态码
    if (response.data.code !== 200) {
      ElMessage.error(response.data.message || '请求失败')
      return Promise.reject(new Error(response.data.message || '请求失败'))
    }

    return response.data
  },
  (error) => {
    console.error('响应错误:', error)

    let message = '网络错误'

    if (error.response) {
      // 服务器响应错误
      const { status, data } = error.response

      switch (status) {
        case 400:
          message = data.detail || '请求参数错误'
          break
        case 401:
          message = '未授权访问'
          break
        case 403:
          message = '禁止访问'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = data.detail || `请求失败 (${status})`
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      message = '网络连接超时，请检查网络连接'
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// 通用API方法
export const apiGet = <T = any>(url: string, params?: any): Promise<ApiResponse<T>> => {
  return api.get(url, { params })
}

export const apiPost = <T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> => {
  return api.post(url, data, config)
}

export const apiPut = <T = any>(url: string, data?: any): Promise<ApiResponse<T>> => {
  return api.put(url, data)
}

export const apiDelete = <T = any>(url: string): Promise<ApiResponse<T>> => {
  return api.delete(url)
}

// 文件上传方法
export const uploadFile = (url: string, formData: FormData, onProgress?: (percent: number) => void): Promise<ApiResponse> => {
  return api.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percent)
      }
    }
  })
}

export default api