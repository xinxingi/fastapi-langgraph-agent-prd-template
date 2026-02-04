/**
 * 框架层应用配置
 * 
 * 对应后端 app/core/config.py
 */

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  apiTimeout: 30000,
  tokenKey: 'access_token',
  enableRegistration: import.meta.env.VITE_ENABLE_REGISTRATION === 'true',
}
