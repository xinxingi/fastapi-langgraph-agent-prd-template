/**
 * 框架层 API 响应类型
 */

export interface ApiResponse<T> {
  data?: T
  error?: string
}
