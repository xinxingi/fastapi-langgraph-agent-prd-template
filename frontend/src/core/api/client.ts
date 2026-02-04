/**
 * 框架层 HTTP 客户端
 * 
 * 使用 axios 进行 HTTP 请求，自动处理认证和错误
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { config } from '../config'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: config.apiBaseUrl,
      timeout: config.apiTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // 请求拦截器：自动添加 token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = this.getToken()
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error: AxiosError) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器：统一错误处理
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<{ detail: string }>) => {
        const message = error.response?.data?.detail || error.message || '请求失败'
        
        // 401 未授权：清除 token 并跳转登录
        if (error.response?.status === 401) {
          this.clearToken()
          ElMessage.error('登录已过期，请重新登录')
          window.location.href = '/login'
        } else {
          ElMessage.error(message)
        }

        return Promise.reject(error)
      }
    )
  }

  getToken(): string | null {
    return localStorage.getItem(config.tokenKey)
  }

  setToken(token: string) {
    localStorage.setItem(config.tokenKey, token)
  }

  clearToken() {
    localStorage.removeItem(config.tokenKey)
  }

  getInstance(): AxiosInstance {
    return this.client
  }
}

export const apiClient = new ApiClient()
export default apiClient.getInstance()
