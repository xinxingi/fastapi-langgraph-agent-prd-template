/**
 * 项目管理 TypeScript 类型定义
 * 
 * 对应后端 app/core/auth/schemas.py 中的项目相关模型
 */

export interface ProjectCreate {
  name: string
  description?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
  is_active?: boolean
}

export interface ProjectResponse {
  id: number
  name: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ProjectListResponse {
  items: ProjectResponse[]
  total: number
  skip: number
  limit: number
}

export interface AssignProjectToUser {
  user_id: number
  project_id: number
  role?: string
}

export interface AssignProjectToApiKey {
  api_key_id: number
  project_id: number
}

export interface UserProjectResponse {
  id: number
  user_id: number
  project_id: number
  role: string
  created_at: string
  project?: ProjectResponse
}

export interface ApiKeyProjectResponse {
  id: number
  api_key_id: number
  project_id: number
  created_at: string
  project?: ProjectResponse
}
