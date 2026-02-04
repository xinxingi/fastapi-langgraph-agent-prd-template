<template>
  <div class="token-management-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>API Key 管理</h2>
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </template>

      <el-alert
        v-if="createdToken"
        title="API Key 创建成功"
        type="success"
        :closable="false"
        style="margin-bottom: 20px"
      >
        <template #default>
          <p style="margin: 8px 0">
            <strong>请妥善保存以下 API Key，关闭后将无法再次查看：</strong>
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
          <p style="margin: 8px 0; font-size: 12px; color: #909399">
            API Key 名称: {{ createdToken.name }}<br>
            过期时间: {{ formatDate(createdToken.expires_at) }}<br>
            使用方式: Authorization: Bearer {{ createdToken.token.substring(0, 15) }}...
          </p>
        </template>
      </el-alert>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="140px"
        style="max-width: 600px"
      >
        <el-form-item label="API Key 名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="例如：开发环境 API Key"
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item label="有效期（天）" prop="expires_in_days">
          <el-input-number
            v-model="form.expires_in_days"
            :min="1"
            :max="27000"
            :disabled="loading"
          />
          <span style="margin-left: 8px; color: #909399; font-size: 12px">
            默认 90 天，最长可设置到 2099 年
          </span>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleCreateToken"
          >
            创建 API Key
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div class="info-section">
        <h3>什么是 API Key？</h3>
        <p>API Key 是长期有效的密钥（sk-xxx 格式），用于服务器到服务器的 API 调用。</p>
        <p><strong>与 JWT Token 的区别：</strong></p>
        <ul>
          <li><strong>JWT Token</strong>：登录后获得的短期会话令牌（30天），用于前端访问</li>
          <li><strong>API Key</strong>：长期有效的密钥（默认90天），用于后端服务集成</li>
        </ul>
        <p><strong>使用方式：</strong>两者都通过 Bearer 认证方案传递</p>
        <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">Authorization: Bearer sk-xxxxxxxxxx</pre>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/core/auth'
import { useTokenManagement } from '../composables/useTokenManagement'
import type { ApiKeyResponse } from '@/core/types'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { format } from 'date-fns'

const router = useRouter()
const authStore = useAuthStore()
const { loading, createToken } = useTokenManagement()

const formRef = ref<FormInstance>()
const createdToken = ref<ApiKeyResponse | null>(null)

const form = reactive({
  name: '',
  expires_in_days: 90,
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入 API Key 名称', trigger: 'blur' },
    { max: 100, message: 'API Key 名称最多 100 个字符', trigger: 'blur' },
  ],
  expires_in_days: [
    { required: true, message: '请输入有效期', trigger: 'blur' },
  ],
}

const handleCreateToken = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    const result = await createToken({
      name: form.name,
      expires_in_days: form.expires_in_days,
    })

    if (result) {
      createdToken.value = result
      resetForm()
    }
  })
}

const resetForm = () => {
  form.name = ''
  form.expires_in_days = 90
  formRef.value?.clearValidate()
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

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.token-management-container {
  max-width: 900px;
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

.info-section {
  margin-top: 20px;
}

.info-section h3 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 16px;
}

.info-section p {
  margin: 8px 0;
  line-height: 1.6;
  color: #606266;
}

.info-section ul {
  margin: 10px 0;
  padding-left: 24px;
}

.info-section li {
  margin: 6px 0;
  line-height: 1.6;
  color: #606266;
}

.info-section pre {
  margin: 10px 0;
  font-size: 13px;
}
</style>
