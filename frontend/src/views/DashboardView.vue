<template>
  <main-layout>
    <div class="dashboard">
      <el-row :gutter="20">
        <el-col :span="24">
          <h1>欢迎使用 FastAPI LangGraph Agent</h1>
        </el-col>
      </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 项目统计 -->
      <el-col :xs="24" :sm="12" :md="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <el-icon :size="24" color="#409EFF">
                <Folder />
              </el-icon>
              <span>项目管理</span>
            </div>
          </template>
          <div class="stat-content">
            <div class="stat-number">{{ projectStore.total }}</div>
            <div class="stat-label">总项目数</div>
            <el-button type="primary" link @click="goToProjects">
              查看详情 →
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- API Key 统计 -->
      <el-col :xs="24" :sm="12" :md="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <el-icon :size="24" color="#67C23A">
                <Key />
              </el-icon>
              <span>API Keys</span>
            </div>
          </template>
          <div class="stat-content">
            <div class="stat-number">{{ apiKeyStore.total }}</div>
            <div class="stat-label">API Key 数量</div>
            <el-button type="success" link @click="goToTokens">
              查看详情 →
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 快速操作 -->
      <el-col :xs="24" :sm="12" :md="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <el-icon :size="24" color="#E6A23C">
                <Lightning />
              </el-icon>
              <span>快速操作</span>
            </div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="goToProjects" style="width: 100%; margin-bottom: 10px">
              创建新项目
            </el-button>
            <el-button type="success" @click="goToTokens" style="width: 100%">
              创建 API Key
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统信息 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>系统信息</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="用户邮箱">
              {{ authStore.token ? '已登录' : '未登录' }}
            </el-descriptions-item>
            <el-descriptions-item label="认证状态">
              <el-tag :type="authStore.isAuthenticated ? 'success' : 'danger'">
                {{ authStore.isAuthenticated ? '已认证' : '未认证' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="项目状态">
              <el-tag type="success">{{ activeProjects }} 个激活</el-tag>
              <el-tag type="info" style="margin-left: 10px">{{ inactiveProjects }} 个未激活</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="API Keys 状态">
              <el-tag type="success">{{ activeApiKeys }} 个有效</el-tag>
              <el-tag type="warning" style="margin-left: 10px">{{ revokedApiKeys }} 个已吊销</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
  </main-layout>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Folder, Key, Lightning } from '@element-plus/icons-vue'
import { useAuthStore } from '@/core/auth'
import { useProjectStore } from '@/core/project/store'
import { useApiKeyStore } from '@/core/auth/apiKeyStore'
import MainLayout from '@/layouts/MainLayout.vue'

const router = useRouter()
const authStore = useAuthStore()
const projectStore = useProjectStore()
const apiKeyStore = useApiKeyStore()

// 计算统计数据
const activeProjects = computed(() => projectStore.activeProjects.length)
const inactiveProjects = computed(() => projectStore.inactiveProjects.length)
const activeApiKeys = computed(() => apiKeyStore.apiKeys.filter(k => !k.revoked).length)
const revokedApiKeys = computed(() => apiKeyStore.apiKeys.filter(k => k.revoked).length)

// 加载数据
onMounted(async () => {
  try {
    await Promise.all([
      projectStore.loadProjects(),
      apiKeyStore.loadApiKeys(),
    ])
  } catch (error) {
    console.error('加载仪表板数据失败:', error)
  }
})

// 导航方法
function goToProjects() {
  router.push('/projects')
}

function goToTokens() {
  router.push('/tokens')
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

h1 {
  font-size: 28px;
  color: #303133;
  margin: 0;
}

.stat-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 16px;
}

.stat-content {
  text-align: center;
  padding: 20px 0;
}

.stat-number {
  font-size: 48px;
  font-weight: 700;
  color: #409EFF;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 15px;
}

.quick-actions {
  padding: 10px;
}
</style>
