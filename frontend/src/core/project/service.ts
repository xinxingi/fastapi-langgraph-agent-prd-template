/**
 * 项目管理 API 服务
 * 
 * 提供项目、用户-项目关联、API Key-项目关联的所有 API 调用
 */

import apiClient from '../api/client'
import type {
  ProjectCreate,
  ProjectUpdate,
  ProjectResponse,
  ProjectListResponse,
  AssignProjectToUser,
  AssignProjectToApiKey,
  UserProjectResponse,
  ApiKeyProjectResponse,
} from '../types/project'

class ProjectService {
  private baseUrl = '/api/v1/projects'

  // ==================== 项目管理 ====================

  /**
   * 创建新项目
   */
  async createProject(data: ProjectCreate): Promise<ProjectResponse> {
    const response = await apiClient.post<ProjectResponse>(this.baseUrl + '/', data)
    return response.data
  }

  /**
   * 获取项目列表
   */
  async listProjects(params: {
    skip?: number
    limit?: number
    is_active?: boolean
  } = {}): Promise<ProjectListResponse> {
    const response = await apiClient.get<ProjectListResponse>(this.baseUrl + '/', { params })
    return response.data
  }

  /**
   * 获取项目详情
   */
  async getProject(projectId: number): Promise<ProjectResponse> {
    const response = await apiClient.get<ProjectResponse>(`${this.baseUrl}/${projectId}`)
    return response.data
  }

  /**
   * 更新项目
   */
  async updateProject(projectId: number, data: ProjectUpdate): Promise<ProjectResponse> {
    const response = await apiClient.put<ProjectResponse>(`${this.baseUrl}/${projectId}`, data)
    return response.data
  }

  /**
   * 删除项目
   */
  async deleteProject(projectId: number): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(`${this.baseUrl}/${projectId}`)
    return response.data
  }

  // ==================== 用户-项目关联管理 ====================

  /**
   * 为用户分配项目
   */
  async assignProjectToUser(data: AssignProjectToUser): Promise<UserProjectResponse> {
    const response = await apiClient.post<UserProjectResponse>(
      `${this.baseUrl}/assign-user`,
      data
    )
    return response.data
  }

  /**
   * 从用户移除项目
   */
  async removeProjectFromUser(userId: number, projectId: number): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(
      `${this.baseUrl}/remove-user/${userId}/${projectId}`
    )
    return response.data
  }

  /**
   * 获取用户的所有项目
   */
  async getUserProjects(params: {
    userId: number
    skip?: number
    limit?: number
  }): Promise<UserProjectResponse[]> {
    const response = await apiClient.get<UserProjectResponse[]>(
      `${this.baseUrl}/user-projects/${params.userId}`,
      {
        params: {
          skip: params.skip,
          limit: params.limit,
        },
      }
    )
    return response.data
  }

  // ==================== API Key-项目关联管理 ====================

  /**
   * 为 API Key 分配项目
   */
  async assignProjectToApiKey(data: AssignProjectToApiKey): Promise<ApiKeyProjectResponse> {
    const response = await apiClient.post<ApiKeyProjectResponse>(
      `${this.baseUrl}/assign-api-key`,
      data
    )
    return response.data
  }

  /**
   * 从 API Key 移除项目
   */
  async removeProjectFromApiKey(
    apiKeyId: number,
    projectId: number
  ): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(
      `${this.baseUrl}/remove-api-key/${apiKeyId}/${projectId}`
    )
    return response.data
  }

  /**
   * 获取 API Key 的所有项目
   */
  async getApiKeyProjects(params: {
    apiKeyId: number
    skip?: number
    limit?: number
  }): Promise<ApiKeyProjectResponse[]> {
    const response = await apiClient.get<ApiKeyProjectResponse[]>(
      `${this.baseUrl}/api-key-projects/${params.apiKeyId}`,
      {
        params: {
          skip: params.skip,
          limit: params.limit,
        },
      }
    )
    return response.data
  }

  /**
   * 获取项目的所有 API Key
   */
  async getProjectApiKeys(params: {
    projectId: number
    skip?: number
    limit?: number
  }): Promise<ApiKeyProjectResponse[]> {
    const response = await apiClient.get<ApiKeyProjectResponse[]>(
      `${this.baseUrl}/${params.projectId}/api-keys`,
      {
        params: {
          skip: params.skip,
          limit: params.limit,
        },
      }
    )
    return response.data
  }
}

export const projectService = new ProjectService()
export default projectService
