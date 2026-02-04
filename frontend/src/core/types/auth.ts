/**
 * 框架层 TypeScript 类型定义
 * 
 * 对应后端 app/core/auth/schemas.py
 * 
 * 注意：Bearer 是 HTTP 认证方案，用于在 Authorization Header 中传递令牌
 * - JWT Token: 短期会话令牌（登录后获得）
 * - API Key: 长期 API 密钥（sk-xxx 格式）
 * 两者都使用 Bearer 方案传递：Authorization: Bearer <token>
 */

export interface Token {
  access_token: string
  token_type: string
  expires_at: string
}

export interface TokenResponse {
  access_token: string  // JWT Token
  expires_at: string
}

export interface UserCreate {
  email: string
  password: string
}

export interface UserResponse {
  id: number
  email: string
  message?: string
}

export interface ApiKeyCreate {
  name: string
  expires_in_days?: number
}

export interface ApiKeyUpdate {
  expires_in_days: number
}

export interface ApiKeyResponse {
  id: number
  name: string
  token: string  // sk-xxx 格式的 API Key
  expires_at: string
  created_at: string
}

export interface ApiKeyListItem {
  id: number
  name: string
  expires_at: string
  created_at: string
  revoked: boolean
}

// 保持向后兼容的别名
export type BearerTokenCreate = ApiKeyCreate
export type BearerTokenResponse = ApiKeyResponse

export interface ApiError {
  detail: string
}
