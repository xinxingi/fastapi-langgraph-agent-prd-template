/**
 * API Key 管理 Store
 * 
 * 使用 Pinia 管理 API Key 状态
 */

import { defineStore } from 'pinia'
import { authService } from './service'
import type { ApiKeyListItem } from '../types'

interface ApiKeyState {
  apiKeys: ApiKeyListItem[]
  loading: boolean
  total: number
}

export const useApiKeyStore = defineStore('apiKey', {
  state: (): ApiKeyState => ({
    apiKeys: [],
    loading: false,
    total: 0,
  }),

  getters: {
    activeApiKeys: (state) => state.apiKeys.filter(key => !key.revoked),
    revokedApiKeys: (state) => state.apiKeys.filter(key => key.revoked),
  },

  actions: {
    async loadApiKeys(skip: number = 0, limit: number = 100) {
      this.loading = true
      try {
        const response = await authService.listApiKeys({ skip, limit })
        this.apiKeys = response.items
        this.total = response.total
      } catch (error) {
        console.error('加载 API Keys 失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async createApiKey(name: string, expiresInDays?: number) {
      const response = await authService.createApiKey({ name, expires_in_days: expiresInDays })
      await this.loadApiKeys()
      return response
    },

    async revokeApiKey(apiKeyId: number) {
      await authService.revokeApiKey(apiKeyId)
      await this.loadApiKeys()
    },

    async deleteApiKey(apiKeyId: number) {
      await authService.deleteApiKey(apiKeyId)
      await this.loadApiKeys()
    },

    reset() {
      this.apiKeys = []
      this.total = 0
      this.loading = false
    },
  },
})
