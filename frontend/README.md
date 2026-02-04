# FastAPI LangGraph Agent - Frontend

基于 Vue 3 + TypeScript + Vite + Element Plus 的前端应用，提供用户认证和 Token 管理功能。

## 目录结构

```
frontend/
├── src/
│   ├── core/              # 框架层（架构代码）
│   │   ├── api/          # HTTP 客户端
│   │   ├── auth/         # 认证模块（框架核心功能）
│   │   │   ├── views/         # 登录、注册、Token管理页面
│   │   │   ├── composables/   # Token管理业务逻辑
│   │   │   ├── service.ts     # 认证服务
│   │   │   └── store.ts       # 认证状态管理
│   │   ├── config/       # 应用配置
│   │   └── types/        # TypeScript 类型定义
│   ├── business/         # 业务层（用于未来业务模块）
│   ├── router/           # 路由配置
│   ├── App.vue           # 根组件
│   └── main.ts           # 应用入口
├── index.html
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 技术栈

- **Vue 3.4+** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全
- **Vite** - 极速开发服务器和构建工具
- **Vue Router** - 官方路由管理
- **Pinia** - 官方状态管理
- **Element Plus** - 企业级 UI 组件库
- **Axios** - HTTP 客户端
- **date-fns** - 日期格式化

## 功能特性

- ✅ 用户注册
- ✅ 用户登录
- ✅ 用户注销
- ✅ API Key 创建（Bearer 认证传输）
- ✅ 自动 Token 管理
- ✅ 路由守卫
- ✅ 统一错误处理

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

应用将在 http://localhost:3000 启动

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 环境配置

复制 `.env.example` 为 `.env.development` 或 `.env.production`：

```bash
cp .env.example .env.development
```

编辑环境变量：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 代码规范

### 目录组织原则

- **core/** - 框架层架构代码，包含认证、API客户端等核心功能
- **business/** - 业务层代码，按具体业务模块组织（目前为空，预留给未来业务功能）

**重要说明**：登录、注册、Token管理属于框架核心功能，放在 `core/auth` 目录下

### 命名约定

- 组件文件：PascalCase（例如：`LoginView.vue`）
- 工具文件：camelCase（例如：`apiClient.ts`）
- Composables：use 前缀（例如：`useTokenManagement.ts`）
- Store：use 前缀 + Store 后缀（例如：`useAuthStore`）

### TypeScript

- 所有类型定义放在 `core/types/` 目录
- 使用 interface 而非 type（除非必要）
- 启用严格模式

## API 对接

前端与后端 API 的对应关系：

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/tokens` - 创建 API Key
- `DELETE /api/v1/auth/tokens/{token_id}` - 撤销 API Key

**说明**：所有 Token（JWT 和 API Key）都通过 Bearer 认证方案传输：`Authorization: Bearer <token>`

## 路由

- `/` - 重定向到登录页
- `/login` - 登录页面
- `/register` - 注册页面
- `/tokens` - Token 管理页面（需要认证）

## 许可证

MIT
