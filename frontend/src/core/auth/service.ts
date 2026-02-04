/**
 * 框架层认证服务
 * 
 * 对应后端 app/core/auth/service.py
 * 提供认证相关的核心功能
 * 
 * 注意：Bearer 是 HTTP 认证方案（RFC 6750），用于传递令牌
 * - JWT Token（登录后）和 API Key（sk-xxx）都通过 Bearer 方案传递
 */

import axios from '../api/client'
import { apiClient } from '../api/client'
import type {
  UserCreate,
  UserResponse,
  TokenResponse,
  ApiKeyCreate,
  ApiKeyResponse,
  ApiKeyListItem,
  ApiKeyUpdate,
} from '../types'

export class AuthService {
  /**
   * 用户注册
   */
  async register(userData: UserCreate): Promise<UserResponse> {
    const response = await axios.post<UserResponse>('/api/v1/auth/register', userData)
    return response.data
  }

  /**
   * 用户登录
   */
  async login(email: string, password: string): Promise<TokenResponse> {
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)
    params.append('grant_type', 'password')

    const response = await axios.post<TokenResponse>('/api/v1/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    // 保存 token
    if (response.data.access_token) {
      apiClient.setToken(response.data.access_token)
    }

    return response.data
  }

  /**
   * 用户注销
   */
  logout() {
    apiClient.clearToken()
  }

  /**
   * 创建 API Key（长期 API 密钥）
   */
  async createToken(tokenData: ApiKeyCreate): Promise<ApiKeyResponse> {
    const response = await axios.post<ApiKeyResponse>('/api/v1/auth/tokens', tokenData)
    return response.data
  }

  /**
   * 获取 API Key 列表
   */
  async listTokens(): Promise<ApiKeyListItem[]> {
    const response = await axios.get<ApiKeyListItem[]>('/api/v1/auth/list_api_key')
    return response.data
  }

  /**
   * 更新 API Key
   */
  async updateToken(tokenId: number, updateData: ApiKeyUpdate): Promise<ApiKeyListItem> {
    const response = await axios.put<ApiKeyListItem>(`/api/v1/auth/tokens/${tokenId}`, updateData)
    return response.data
  }

  /**
   * 撤销 API Key
   */
  async revokeToken(tokenId: number): Promise<{ message: string }> {
    const response = await axios.delete<{ message: string }>(`/api/v1/auth/tokens/${tokenId}`)
    return response.data
  }

  /**
   * 获取当前 token
   */
  getToken(): string | null {
    return apiClient.getToken()
  }

  /**
   * 检查是否已登录
   */
  isAuthenticated(): boolean {
    return !!this.getToken()
  }
}

export const authService = new AuthService()
