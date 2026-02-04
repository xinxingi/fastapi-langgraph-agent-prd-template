/**
 * 框架层认证 Store
 * 
 * 使用 Pinia 管理认证状态
 */

import { defineStore } from 'pinia'
import { authService } from './service'
import type { TokenResponse, UserCreate } from '../types'

interface AuthState {
  token: string | null
  expiresAt: string | null
  isAuthenticated: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: authService.getToken(),
    expiresAt: null,
    isAuthenticated: authService.isAuthenticated(),
  }),

  actions: {
    async register(userData: UserCreate) {
      const response = await authService.register(userData)
      return response
    },

    async login(email: string, password: string) {
      const response = await authService.login(email, password)
      this.token = response.access_token
      this.expiresAt = response.expires_at
      this.isAuthenticated = true
      return response
    },

    logout() {
      authService.logout()
      this.token = null
      this.expiresAt = null
      this.isAuthenticated = false
    },

    checkAuth() {
      this.isAuthenticated = authService.isAuthenticated()
      this.token = authService.getToken()
    },
  },
})
