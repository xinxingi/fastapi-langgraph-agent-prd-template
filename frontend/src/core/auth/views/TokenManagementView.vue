<template>
  <div class="token-management-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>API Key 管理</h2>
          <div>
            <el-button type="primary" @click="openCreateDialog">创建 API Key</el-button>
            <el-button type="danger" @click="handleLogout">退出登录</el-button>
          </div>
        </div>
      </template>

      <!-- 新创建的 API Key 提示 -->
      <el-alert
        v-if="createdToken"
        title="API Key 创建成功"
        type="success"
        :closable="true"
        @close="createdToken = null"
        style="margin-bottom: 20px"
      >
        <template #default>
          <p style="margin: 8px 0">
            <strong>请妥善保存以下 API Key：</strong>
          </p>
          <el-input
            :model-value="createdToken.token"
            readonly
            style="margin-top: 8px"
          >
            <template #append>
              <el-button @click="copyToken(createdToken.token)">复制</el-button>
            </template>
          </el-input>
        </template>
      </el-alert>

      <!-- 搜索和筛选 -->
      <div style="margin-bottom: 16px; display: flex; gap: 16px">
        <el-input
          v-model="searchQuery"
          placeholder="搜索 API Key 名称"
          clearable
          style="max-width: 300px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="statusFilter"
          placeholder="按状态筛选"
          clearable
          style="width: 150px"
        >
          <el-option label="全部" value="" />
          <el-option label="有效" value="valid" />
          <el-option label="已过期" value="expired" />
          <el-option label="已撤销" value="revoked" />
        </el-select>
      </div>

      <!-- API Key 表格 -->
      <el-table
        :data="filteredApiKeys"
        v-loading="loading"
        style="width: 100%"
        :empty-text="loading ? '加载中...' : '暂无数据'"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="过期时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.expires_at) }}
          </template>
        </el-table-column>
        <el-table-column label="最后使用" width="180">
          <template #default="{ row }">
            {{ row.last_used_at ? formatDate(row.last_used_at) : '从未使用' }}
          </template>
        </el-table-column>
        <el-table-column label="剩余时间" width="150">
          <template #default="{ row }">
            <span v-if="row.revoked" style="color: #909399">已撤销</span>
            <span v-else :style="{ color: isExpired(row.expires_at) ? '#F56C6C' : '#67C23A' }">
              {{ getTimeRemaining(row.expires_at) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.revoked" type="danger">已撤销</el-tag>
            <el-tag v-else-if="isExpired(row.expires_at)" type="warning">已过期</el-tag>
            <el-tag v-else type="success">有效</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Key" min-width="200">
          <template #default="{ row }">
            <span style="font-family: monospace; color: #909399; font-size: 12px">
              {{ row.revoked ? '已撤销' : 'sk-***...' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.revoked"
              type="primary"
              size="small"
              link
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="!row.revoked"
              type="danger"
              size="small"
              link
              @click="handleRevoke(row)"
            >
              删除
            </el-button>
            <span v-else style="color: #909399; font-size: 12px">-</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="total > 0"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 20px; justify-content: flex-end"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 创建 API Key 对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建 API Key"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="140px"
      >
        <el-form-item label="API Key 名称" prop="name">
          <el-input
            v-model="createForm.name"
            placeholder="例如：开发环境 API Key"
            :disabled="submitLoading"
          />
        </el-form-item>

        <el-form-item label="有效期（天）" prop="expires_in_days">
          <el-input-number
            v-model="createForm.expires_in_days"
            :min="1"
            :max="27000"
            :disabled="submitLoading"
            style="width: 100%"
          />
          <div style="margin-top: 8px; color: #909399; font-size: 12px">
            默认 90 天，最长可设置到 2099 年
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitLoading"
          @click="handleCreateToken"
        >
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑 API Key 对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑 API Key"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="140px"
      >
        <el-form-item label="API Key 名称">
          <el-input :model-value="editingKey?.name" disabled />
        </el-form-item>

        <el-form-item label="当前过期时间">
          <el-input :model-value="editingKey ? formatDate(editingKey.expires_at) : ''" disabled />
        </el-form-item>

        <el-form-item label="新的有效期（天）" prop="expires_in_days">
          <el-input-number
            v-model="editForm.expires_in_days"
            :min="1"
            :max="27000"
            :disabled="submitLoading"
            style="width: 100%"
          />
          <div style="margin-top: 8px; color: #909399; font-size: 12px">
            从现在起计算，最长可设置到 2099 年
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitLoading"
          @click="handleUpdateToken"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/core/auth'
import { authService } from '../service'
import type { ApiKeyResponse, ApiKeyListItem } from '@/core/types'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { format } from 'date-fns'
import { Search } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const createFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()
const loading = ref(false)
const submitLoading = ref(false)
const createDialogVisible = ref(false)
const editDialogVisible = ref(false)
const createdToken = ref<ApiKeyResponse | null>(null)
const apiKeys = ref<ApiKeyListItem[]>([])
const editingKey = ref<ApiKeyListItem | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchQuery = ref('')
const statusFilter = ref('')

const createForm = reactive({
  name: '',
  expires_in_days: 90,
})

const editForm = reactive({
  expires_in_days: 90,
})

const createRules: FormRules = {
  name: [
    { required: true, message: '请输入 API Key 名称', trigger: 'blur' },
    { max: 100, message: 'API Key 名称最多 100 个字符', trigger: 'blur' },
  ],
  expires_in_days: [
    { required: true, message: '请输入有效期', trigger: 'blur' },
  ],
}

const editRules: FormRules = {
  expires_in_days: [
    { required: true, message: '请输入有效期', trigger: 'blur' },
  ],
}

// 计算过滤后的 API Key 列表
const filteredApiKeys = computed(() => {
  return apiKeys.value.filter(key => {
    // 按名称搜索
    const matchesSearch = !searchQuery.value || 
      key.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    // 按状态筛选
    let matchesStatus = true
    if (statusFilter.value) {
      if (statusFilter.value === 'valid') {
        matchesStatus = !key.revoked && !isExpired(key.expires_at)
      } else if (statusFilter.value === 'expired') {
        matchesStatus = !key.revoked && isExpired(key.expires_at)
      } else if (statusFilter.value === 'revoked') {
        matchesStatus = key.revoked
      }
    }
    
    return matchesSearch && matchesStatus
  })
})

// 加载 API Key 列表
const loadApiKeys = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const response = await authService.listTokens(skip, pageSize.value)
    apiKeys.value = response.items
    total.value = response.total
  } catch (error: any) {
    // 错误已由全局错误处理器显示，这里不需要再次显示
    console.error('Failed to load API keys:', error)
  } finally {
    loading.value = false
  }
}

// 处理页码变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadApiKeys()
}

// 处理每页数量变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1  // 重置到第一页
  loadApiKeys()
}

// 打开创建对话框
const openCreateDialog = () => {
  createForm.name = ''
  createForm.expires_in_days = 90
  createFormRef.value?.clearValidate()
  createDialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (row: ApiKeyListItem) => {
  editingKey.value = row
  editForm.expires_in_days = 90
  editFormRef.value?.clearValidate()
  editDialogVisible.value = true
}

// 创建 API Key
const handleCreateToken = async () => {
  if (!createFormRef.value) return

  await createFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      const result = await authService.createToken({
        name: createForm.name,
        expires_in_days: createForm.expires_in_days,
      })

      createdToken.value = result
      createDialogVisible.value = false
      ElMessage.success('API Key 创建成功')
      
      // 重新加载列表，回到第一页
      currentPage.value = 1
      await loadApiKeys()
    } catch (error: any) {
      // 错误已由全局错误处理器显示，这里不需要再次显示
      console.error('Failed to create API key:', error)
    } finally {
      submitLoading.value = false
    }
  })
}

// 更新 API Key
const handleUpdateToken = async () => {
  if (!editFormRef.value || !editingKey.value) return

  await editFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitLoading.value = true
    try {
      await authService.updateToken(editingKey.value!.id, {
        expires_in_days: editForm.expires_in_days,
      })

      editDialogVisible.value = false
      ElMessage.success('API Key 更新成功')
      
      // 重新加载列表
      await loadApiKeys()
    } catch (error: any) {
      // 错误已由全局错误处理器显示，这里不需要再次显示
      console.error('Failed to update API key:', error)
    } finally {
      submitLoading.value = false
    }
  })
}

// 撤销 API Key
const handleRevoke = async (row: ApiKeyListItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 API Key "${row.name}" 吗？删除后将无法恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await authService.revokeToken(row.id)
    ElMessage.success('API Key 已删除')
    
    // 重新加载列表
    await loadApiKeys()
  } catch (error: any) {
    if (error === 'cancel') return
    // 错误已由全局错误处理器显示，这里不需要再次显示
    console.error('Failed to revoke API key:', error)
  }
}

const copyToken = async (token: string) => {
  try {
    await navigator.clipboard.writeText(token)
    ElMessage.success('API Key 已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

const formatDate = (dateStr: string) => {
  return format(new Date(dateStr), 'yyyy-MM-dd HH:mm:ss')
}

const isExpired = (dateStr: string) => {
  return new Date(dateStr) < new Date()
}

// 计算并格式化剩余时间
const getTimeRemaining = (expiresAt: string): string => {
  const now = new Date()
  const expiry = new Date(expiresAt)
  const diffMs = expiry.getTime() - now.getTime()

  if (diffMs <= 0) {
    return '已过期'
  }

  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))

  if (days > 365) {
    const years = Math.floor(days / 365)
    const remainingDays = days % 365
    return `${years} 年 ${remainingDays} 天`
  } else if (days > 30) {
    const months = Math.floor(days / 30)
    const remainingDays = days % 30
    return `${months} 个月 ${remainingDays} 天`
  } else if (days > 0) {
    return `${days} 天 ${hours} 小时`
  } else if (hours > 0) {
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
    return `${hours} 小时 ${minutes} 分钟`
  } else {
    const minutes = Math.floor(diffMs / (1000 * 60))
    return `${minutes} 分钟`
  }
}

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

// 页面加载时获取列表
onMounted(() => {
  loadApiKeys()
})
</script>

<style scoped>
.token-management-container {
  max-width: 1400px;
  margin: 40px auto;
  padding: 0 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  color: #303133;
}
</style>
