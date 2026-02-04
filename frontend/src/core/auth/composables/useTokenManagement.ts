/**
 * 业务层：Token 管理 Composable
 * 
 * 处理 token 创建和管理的业务逻辑
 */

import { ref } from 'vue'
import { authService } from '@/core/auth'
import type { BearerTokenCreate, BearerTokenResponse } from '@/core/types'
import { ElMessage } from 'element-plus'

export function useTokenManagement() {
  const loading = ref(false)
  const tokens = ref<BearerTokenResponse[]>([])

  const createToken = async (tokenData: BearerTokenCreate): Promise<BearerTokenResponse | null> => {
    loading.value = true
    try {
      const response = await authService.createToken(tokenData)
      ElMessage.success('Token 创建成功')
      return response
    } catch (error) {
      console.error('Token creation failed:', error)
      return null
    } finally {
      loading.value = false
    }
  }

  const revokeToken = async (tokenId: number): Promise<boolean> => {
    loading.value = true
    try {
      await authService.revokeToken(tokenId)
      ElMessage.success('Token 已撤销')
      return true
    } catch (error) {
      console.error('Token revocation failed:', error)
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    tokens,
    createToken,
    revokeToken,
  }
}
