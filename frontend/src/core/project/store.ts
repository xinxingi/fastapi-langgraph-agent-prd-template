/**
 * 项目管理 Pinia Store
 * 
 * 管理项目状态和操作
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { projectService } from './service'
import type {
  ProjectResponse,
  ProjectCreate,
  ProjectUpdate,
  UserProjectResponse,
  ApiKeyProjectResponse,
} from '../types/project'

export const useProjectStore = defineStore('project', () => {
  // ==================== 状态 ====================
  const projects = ref<ProjectResponse[]>([])
  const currentProject = ref<ProjectResponse | null>(null)
  const loading = ref(false)
  const total = ref(0)

  // ==================== 计算属性 ====================
  const activeProjects = computed(() => 
    projects.value.filter(p => p.is_active)
  )

  const inactiveProjects = computed(() => 
    projects.value.filter(p => !p.is_active)
  )

  // ==================== 项目管理操作 ====================

  /**
   * 加载项目列表
   */
  async function loadProjects(params: {
    skip?: number
    limit?: number
    is_active?: boolean
  } = {}) {
    try {
      loading.value = true
      const response = await projectService.listProjects(params)
      projects.value = response.items
      total.value = response.total
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '加载项目列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建项目
   */
  async function createProject(data: ProjectCreate) {
    try {
      loading.value = true
      const project = await projectService.createProject(data)
      projects.value.unshift(project)
      total.value += 1
      ElMessage.success('项目创建成功')
      return project
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '项目创建失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新项目
   */
  async function updateProject(projectId: number, data: ProjectUpdate) {
    try {
      loading.value = true
      const project = await projectService.updateProject(projectId, data)
      const index = projects.value.findIndex(p => p.id === projectId)
      if (index !== -1) {
        projects.value[index] = project
      }
      if (currentProject.value?.id === projectId) {
        currentProject.value = project
      }
      ElMessage.success('项目更新成功')
      return project
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '项目更新失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除项目
   */
  async function deleteProject(projectId: number) {
    try {
      loading.value = true
      await projectService.deleteProject(projectId)
      projects.value = projects.value.filter(p => p.id !== projectId)
      total.value -= 1
      if (currentProject.value?.id === projectId) {
        currentProject.value = null
      }
      ElMessage.success('项目删除成功')
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '项目删除失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取项目详情
   */
  async function getProject(projectId: number) {
    try {
      loading.value = true
      const project = await projectService.getProject(projectId)
      currentProject.value = project
      return project
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '加载项目详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 重置状态
   */
  function reset() {
    projects.value = []
    currentProject.value = null
    loading.value = false
    total.value = 0
  }

  return {
    // 状态
    projects,
    currentProject,
    loading,
    total,
    
    // 计算属性
    activeProjects,
    inactiveProjects,
    
    // 操作
    loadProjects,
    createProject,
    updateProject,
    deleteProject,
    getProject,
    reset,
  }
})
