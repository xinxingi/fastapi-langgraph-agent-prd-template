/**
 * Vue Router 配置
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/core/auth'
import LoginView from '@/core/auth/views/LoginView.vue'
import RegisterView from '@/core/auth/views/RegisterView.vue'
import TokenManagementView from '@/core/auth/views/TokenManagementView.vue'
import ProjectManagementView from '@/core/project/views/ProjectManagementView.vue'
import DashboardView from '@/views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false },
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { requiresAuth: false },
    },
    {
      path: '/tokens',
      name: 'tokens',
      component: TokenManagementView,
      meta: { requiresAuth: true },
    },
    {
      path: '/projects',
      name: 'projects',
      component: ProjectManagementView,
      meta: { requiresAuth: true },
    },
  ],
})

// 路由守卫：检查认证状态
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth

  if (requiresAuth && !authStore.isAuthenticated) {
    // 需要认证但未登录，跳转到登录页
    next('/login')
  } else if (!requiresAuth && authStore.isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    // 已登录用户访问登录/注册页，跳转到仪表板
    next('/dashboard')
  } else {
    next()
  }
})

export default router
