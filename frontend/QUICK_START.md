# 前端快速启动指南

## 项目概览

Vue 3 前端应用，提供用户认证和 Token 管理功能。目录结构遵循后端的组织方式：
- **core/** - 框架层架构代码（认证、API 客户端等核心功能）
- **business/** - 业务层代码（预留给未来业务模块）

**重要**：登录、注册、Token 管理属于框架核心功能，位于 `core/auth` 目录

## 启动步骤

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env.development
```

如需修改后端 API 地址，编辑 `.env.development`：
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 4. 确保后端已启动

前端需要后端 API 支持，请确保后端服务已在 http://localhost:8000 运行：

```bash
# 在项目根目录
cd ..
make dev
```

## 功能页面

1. **注册页面** (`/register`)
   - 用户邮箱注册
   - 密码强度验证（大小写字母+数字+特殊字符）

2. **登录页面** (`/login`)
   - 使用邮箱和密码登录
   - 自动保存 JWT Token

3. **Token 管理页面** (`/tokens`)
   - 创建 API Key（长期有效凭证）
   - 设置 Token 有效期
   - 复制 Token 到剪贴板
   - 退出登录

## 项目结构说明

```
frontend/src/
├── core/                    # 框架层（核心功能）
│   ├── api/                # HTTP 客户端，自动处理认证
│   ├── auth/               # 认证模块（框架核心）
│   │   ├── views/          # 登录、注册、Token管理页面
│   │   ├── composables/    # Token管理业务逻辑
│   │   ├── service.ts      # 认证服务
│   │   └── store.ts        # 认证状态管理
│   ├── config/             # 应用配置
│   └── types/              # TypeScript 类型定义
├── business/               # 业务层（预留给未来业务模块）
├── router/                 # 路由配置（含路由守卫）
├── App.vue                 # 根组件
└── main.ts                 # 应用入口
```

## 技术栈

- Vue 3.4+ (Composition API)
- TypeScript
- Vite
- Vue Router
- Pinia (状态管理)
- Element Plus (UI 组件库)
- Axios (HTTP 客户端)

## 开发命令

```bash
# 开发模式
npm run dev

# 类型检查
npm run type-check

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 与后端对接

前端已配置 Vite 代理，所有 `/api` 请求会转发到后端：

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

## 认证流程

1. 用户在登录页面输入邮箱和密码
2. 前端调用 `POST /api/v1/auth/login`
3. 后端返回 JWT Token
4. Token 保存到 localStorage
5. 后续请求自动在 Header 中携带 `Authorization: Bearer <token>`
6. 路由守卫检查认证状态，未登录用户跳转到登录页

## 常见问题

### 1. 启动失败

检查 Node.js 版本：
```bash
node --version  # 建议 18.0+
```

### 2. API 请求失败

确认后端服务已启动：
```bash
curl http://localhost:8000/api/v1/health
```

### 3. 登录后立即跳回登录页

检查浏览器控制台是否有 CORS 错误，确保后端 CORS 配置正确。

## 下一步

- 在 `business/` 目录添加具体业务模块（如聊天机器人、HR入职等）
- 复用 `core/` 中的认证、API 客户端等框架功能
- 参考 `core/auth` 的组织方式创建新模块
