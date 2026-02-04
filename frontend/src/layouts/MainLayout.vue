<template>
  <el-container class="main-layout">
    <el-header class="header">
      <div class="header-content">
        <div class="logo">
          <h2>FastAPI LangGraph Agent</h2>
        </div>
        <el-menu
          :default-active="activeIndex"
          mode="horizontal"
          :ellipsis="false"
          @select="handleSelect"
          class="nav-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <span>仪表板</span>
          </el-menu-item>
          <el-menu-item index="/projects">
            <el-icon><Folder /></el-icon>
            <span>项目管理</span>
          </el-menu-item>
          <el-menu-item index="/tokens">
            <el-icon><Key /></el-icon>
            <span>API Keys</span>
          </el-menu-item>
        </el-menu>
        <div class="user-section">
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </div>
    </el-header>
    <el-main class="main-content">
      <slot />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { HomeFilled, Folder, Key } from '@element-plus/icons-vue'
import { useAuthStore } from '@/core/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeIndex = ref(route.path)

// 监听路由变化，更新激活的菜单项
watch(
  () => route.path,
  (newPath) => {
    activeIndex.value = newPath
  }
)

function handleSelect(index: string) {
  router.push(index)
}

function handleLogout() {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.header {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0;
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.logo {
  margin-right: 40px;
}

.logo h2 {
  margin: 0;
  font-size: 20px;
  color: #409EFF;
}

.nav-menu {
  flex: 1;
  border-bottom: none;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .logo h2 {
    font-size: 16px;
  }

  .header-content {
    padding: 0 10px;
  }

  .logo {
    margin-right: 20px;
  }
}
</style>
