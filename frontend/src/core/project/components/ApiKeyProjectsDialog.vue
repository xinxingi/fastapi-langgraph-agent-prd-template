<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :title="`管理 API Key 权限 - ${project?.name || ''}`"
    width="800px"
    @close="handleClose"
  >
    <div v-if="project">
      <!-- 添加 API Key 权限 -->
      <el-card class="add-section">
        <template #header>
          <span>为 API Key 分配项目权限</span>
        </template>
        <el-form :inline="true" @submit.prevent="handleAssign">
          <el-form-item label="选择 API Key">
            <el-select
              v-model="selectedApiKeyId"
              placeholder="请选择 API Key"
              style="width: 300px"
              filterable
            >
              <el-option
                v-for="key in availableApiKeys"
                :key="key.id"
                :label="`${key.name}`"
                :value="key.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleAssign" :loading="loading">
              分配权限
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 已分配的 API Key 列表 -->
      <el-card class="list-section">
        <template #header>
          <span>已分配的 API Key</span>
        </template>
        <el-table :data="assignedApiKeys" v-loading="loading" style="width: 100%">
          <el-table-column prop="api_key_id" label="API Key ID" width="120" />
          <el-table-column label="API Key 名称" width="200">
            <template #default="{ row }">
              {{ getApiKeyName(row.api_key_id) }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="分配时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="danger" @click="handleRemove(row)">
                移除权限
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { projectService } from '../service'
import type { ProjectResponse, ApiKeyProjectResponse } from '@/core/types/project'
import type { ApiKeyListItem } from '@/core/types/auth'
import { authService } from '@/core/auth/service'
import { format } from 'date-fns'

interface Props {
  modelValue: boolean
  project: ProjectResponse | null
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'updated'])

const loading = ref(false)
const selectedApiKeyId = ref<number | null>(null)
const assignedApiKeys = ref<ApiKeyProjectResponse[]>([])
const allApiKeys = ref<ApiKeyListItem[]>([])

// 计算可用的 API Key（排除已分配的）
const availableApiKeys = computed(() => {
  const assignedIds = new Set(assignedApiKeys.value.map(a => a.api_key_id))
  return allApiKeys.value.filter(key => !assignedIds.has(key.id) && !key.revoked)
})

// 监听对话框打开
watch(
  () => props.modelValue,
  async (visible) => {
    if (visible && props.project) {
      await loadData()
    }
  }
)

// 加载数据
async function loadData() {
  if (!props.project) return

  try {
    loading.value = true

    // 并行加载已分配的 API Key 和所有 API Key
    const [assigned, all] = await Promise.all([
      projectService.getProjectApiKeys({
        projectId: props.project.id,
        skip: 0,
        limit: 100,
      }),
      authService.listApiKeys({ skip: 0, limit: 100 }),
    ])

    console.log('已分配的 API Keys:', assigned)
    console.log('所有 API Keys:', all)

    assignedApiKeys.value = assigned
    allApiKeys.value = all.items
    
    console.log('可用的 API Keys:', availableApiKeys.value)
  } catch (error: any) {
    console.error('加载数据失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载数据失败')
  } finally {
    loading.value = false
  }
}

// 获取 API Key 名称
function getApiKeyName(apiKeyId: number): string {
  const key = allApiKeys.value.find(k => k.id === apiKeyId)
  return key ? key.name : `API Key ${apiKeyId}`
}

// 格式化日期
function formatDate(dateString: string) {
  return format(new Date(dateString), 'yyyy-MM-dd HH:mm:ss')
}

// 分配权限
async function handleAssign() {
  if (!selectedApiKeyId.value || !props.project) {
    ElMessage.warning('请选择 API Key')
    return
  }

  try {
    loading.value = true
    await projectService.assignProjectToApiKey({
      api_key_id: selectedApiKeyId.value,
      project_id: props.project.id,
    })
    ElMessage.success('权限分配成功')
    selectedApiKeyId.value = null
    await loadData()
    emit('updated')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '权限分配失败')
  } finally {
    loading.value = false
  }
}

// 移除权限
async function handleRemove(assignment: ApiKeyProjectResponse) {
  if (!props.project) return

  try {
    await ElMessageBox.confirm(
      `确定要移除 API Key "${getApiKeyName(assignment.api_key_id)}" 的项目访问权限吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    loading.value = true
    await projectService.removeProjectFromApiKey(assignment.api_key_id, props.project.id)
    ElMessage.success('权限移除成功')
    await loadData()
    emit('updated')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '权限移除失败')
    }
  } finally {
    loading.value = false
  }
}

// 关闭对话框
function handleClose() {
  selectedApiKeyId.value = null
  assignedApiKeys.value = []
  allApiKeys.value = []
}
</script>

<style scoped>
.add-section {
  margin-bottom: 20px;
}

.list-section {
  margin-top: 20px;
}
</style>
