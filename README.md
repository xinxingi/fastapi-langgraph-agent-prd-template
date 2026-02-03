# FastAPI LangGraph Agent 模板

一个生产就绪的 FastAPI 模板，用于构建集成 LangGraph 的 AI 代理应用程序。此模板为构建可扩展、安全且易于维护的 AI 代理服务提供了坚实的基础。

## 🌟 特性

- **生产就绪架构**

  - FastAPI 提供高性能异步 API 端点，具有 uvloop 优化
  - LangGraph 集成用于 AI 代理工作流和状态持久化
  - Langfuse 用于 LLM 可观测性和监控
  - 结构化日志记录，支持环境特定格式和请求上下文
  - 速率限制，每个端点可配置规则
  - PostgreSQL 与 pgvector 用于数据持久化和向量存储
  - Docker 和 Docker Compose 支持
  - Prometheus 指标和 Grafana 仪表板用于监控

- **AI 和 LLM 特性**

  - 使用 mem0ai 和 pgvector 的长期记忆，支持语义记忆存储
  - LLM 服务，使用 tenacity 实现自动重试逻辑
  - 支持多个 LLM 模型（GPT-4o、GPT-4o-mini、GPT-5、GPT-5-mini、GPT-5-nano）
  - 流式响应，支持实时聊天交互
  - 工具调用和函数执行能力

- **安全性**

  - 基于 JWT 的身份验证
  - 会话管理
  - 输入清理
  - CORS 配置
  - 速率限制保护

- **开发者体验**

  - 环境特定配置，自动加载 .env 文件
  - 全面的日志系统，支持上下文绑定
  - 清晰的项目结构，遵循最佳实践
  - 全面的类型提示，提供更好的 IDE 支持
  - 使用 Makefile 命令轻松进行本地开发设置
  - 自动重试逻辑，采用指数退避策略提高弹性

- **模型评估框架**
  - 基于指标的模型输出自动评估
  - 与 Langfuse 集成进行跟踪分析
  - 详细的 JSON 报告，包含成功/失败指标
  - 交互式命令行界面
  - 可自定义的评估指标

## 🚀 快速开始

### 前置要求

- Python 3.13+
- PostgreSQL（[参见数据库设置](#数据库设置)）
- Docker 和 Docker Compose（可选）

### 环境设置

1. 克隆仓库：

```bash
git clone <repository-url>
cd <project-directory>
```

2. 创建并激活虚拟环境：

```bash
uv sync
```

3. 复制示例环境文件：

```bash
cp .env.example .env.[development|staging|production] # 例如 .env.development
```

4. 更新 `.env` 文件的配置（参考 `.env.example`）

### 数据库设置

1. 创建一个 PostgreSQL 数据库（例如 Supabase 或本地 PostgreSQL）
2. 在 `.env` 文件中更新数据库连接设置：

```bash
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=cool_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

- 您无需手动创建表，ORM 会为您处理。但如果遇到任何问题，请运行 `schemas.sql` 文件手动创建表。

### 运行应用程序

#### 本地开发

1. 安装依赖：

```bash
uv sync
```

2. 运行应用程序：

```bash
make [dev|staging|prod] # 例如 make dev
```

3. 访问 Swagger UI：

```bash
http://localhost:8000/docs
```

#### 使用 Docker

1. 使用 Docker Compose 构建并运行：

```bash
make docker-build-env ENV=[development|staging|production] # 例如 make docker-build-env ENV=development
make docker-run-env ENV=[development|staging|production] # 例如 make docker-run-env ENV=development
```

2. 访问监控堆栈：

```bash
# Prometheus 指标
http://localhost:9090

# Grafana 仪表板
http://localhost:3000
默认凭据：
- 用户名：admin
- 密码：admin
```

Docker 设置包括：

- FastAPI 应用程序
- PostgreSQL 数据库
- Prometheus 用于指标收集
- Grafana 用于指标可视化
- 预配置的仪表板：
  - API 性能指标
  - 速率限制统计
  - 数据库性能
  - 系统资源使用

## 📊 模型评估

该项目包含一个强大的评估框架，用于随时间测量和跟踪模型性能。评估器自动从 Langfuse 获取跟踪数据，应用评估指标，并生成详细报告。

### 运行评估

您可以使用提供的 Makefile 命令以不同选项运行评估：

```bash
# 交互式模式，逐步提示
make eval [ENV=development|staging|production]

# 快速模式，使用默认设置（无提示）
make eval-quick [ENV=development|staging|production]

# 不生成报告的评估
make eval-no-report [ENV=development|staging|production]
```

### 评估特性

- **交互式 CLI**：用户友好的界面，带有彩色输出和进度条
- **灵活配置**：设置默认值或在运行时自定义
- **详细报告**：JSON 报告，包含全面的指标：
  - 整体成功率
  - 特定指标的性能
  - 持续时间和时间信息
  - 跟踪级别的成功/失败详情

### 自定义指标

评估指标在 `evals/metrics/prompts/` 中定义为 markdown 文件：

1. 在 prompts 目录中创建一个新的 markdown 文件（例如 `my_metric.md`）
2. 定义评估标准和评分逻辑
3. 评估器将自动发现并应用您的新指标

### 查看报告

报告自动生成在 `evals/reports/` 目录中，文件名包含时间戳：

```
evals/reports/evaluation_report_YYYYMMDD_HHMMSS.json
```

每个报告包括：

- 高级统计数据（总跟踪数、成功率等）
- 每个指标的性能指标
- 用于调试的详细跟踪级别信息

## 🔧 配置

应用程序使用灵活的配置系统，具有环境特定设置：

- `.env.development` - 本地开发设置
- `.env.staging` - 预发布环境设置
- `.env.production` - 生产环境设置

### 环境变量

关键配置变量包括：

```bash
# 应用程序
APP_ENV=development
PROJECT_NAME="FastAPI LangGraph Agent"
DEBUG=true

# 数据库
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mydb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# LLM 配置
OPENAI_API_KEY=your_openai_api_key
DEFAULT_LLM_MODEL=gpt-4o
DEFAULT_LLM_TEMPERATURE=0.7
MAX_TOKENS=4096

# 长期记忆
LONG_TERM_MEMORY_COLLECTION_NAME=agent_memories
LONG_TERM_MEMORY_MODEL=gpt-4o-mini
LONG_TERM_MEMORY_EMBEDDER_MODEL=text-embedding-3-small

# 可观测性
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

# 安全性
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 速率限制
RATE_LIMIT_ENABLED=true
```

## 🧠 长期记忆

应用程序包含一个由 mem0ai 和 pgvector 支持的复杂长期记忆系统：

### 特性

- **语义记忆存储**：基于语义相似性存储和检索记忆
- **用户特定记忆**：每个用户都有自己的隔离记忆空间
- **自动记忆管理**：记忆自动提取、存储和检索
- **向量搜索**：使用 pgvector 进行高效相似性搜索
- **可配置模型**：用于记忆处理和嵌入的独立模型

### 工作原理

1. **记忆添加**：在对话期间，重要信息会自动提取并存储
2. **记忆检索**：根据对话上下文检索相关记忆
3. **记忆搜索**：语义搜索在多个对话中查找相关记忆
4. **记忆更新**：当有新信息时，可以更新现有记忆

## 🤖 LLM 服务

LLM 服务提供强大的、生产就绪的语言模型交互，具有自动重试逻辑和多模型支持。

### 特性

- **多模型支持**：预配置支持 GPT-4o、GPT-4o-mini、GPT-5 及 GPT-5 变体
- **自动重试**：使用 tenacity 实现指数退避重试逻辑
- **推理配置**：GPT-5 模型支持可配置的推理工作级别
- **环境特定调优**：开发环境与生产环境的不同参数
- **回退机制**：当主模型失败时优雅降级

### 支持的模型

| 模型        | 使用场景       | 推理工作量 |
| ----------- | -------------- | ---------- |
| gpt-5       | 复杂推理任务   | 中等       |
| gpt-5-mini  | 平衡性能       | 低         |
| gpt-5-nano  | 快速响应       | 最小       |
| gpt-4o      | 生产工作负载   | 不适用     |
| gpt-4o-mini | 成本效益型任务 | 不适用     |

### 重试配置

- 自动在 API 超时、速率限制和临时错误时重试
- **最大尝试次数**：3 次
- **等待策略**：指数退避（1秒、2秒、4秒）
- **日志记录**：所有重试尝试都会带上下文记录

## 📝 高级日志记录

应用程序使用 structlog 进行结构化、上下文化的日志记录，并自动进行请求跟踪。

### 特性

- **结构化日志记录**：所有日志都具有一致字段的结构化格式
- **请求上下文**：自动绑定 request_id、session_id 和 user_id
- **环境特定格式化**：生产环境使用 JSON，开发环境使用彩色控制台
- **性能跟踪**：自动记录请求持续时间和状态
- **异常跟踪**：完整的堆栈跟踪，保留上下文

### 日志上下文中间件

每个请求自动获取：
- 唯一的请求 ID
- 会话 ID（如果已认证）
- 用户 ID（如果已认证）
- 请求路径和方法
- 响应状态和持续时间

### 日志格式标准

- **事件名称**：使用 lowercase_with_underscores 格式
- **不使用 F-字符串**：将变量作为 kwargs 传递以便正确过滤
- **上下文绑定**：始终包含相关 ID 和上下文
- **适当的级别**：debug、info、warning、error、exception

## ⚡ 性能优化

### uvloop 集成

应用程序使用 uvloop 增强异步性能（通过 Makefile 自动启用）：

**性能改进**：
- 异步操作速度提高 2-4 倍
- I/O 密集型任务延迟更低
- 更好的连接池管理
- 并发请求的 CPU 使用率降低

### 连接池

- **数据库**：异步连接池，可配置池大小
- **LangGraph 检查点**：用于状态持久化的共享连接池
- **Redis**（可选）：用于缓存的连接池

### 缓存策略

- 仅缓存成功响应
- 基于数据波动性的可配置 TTL
- 更新时缓存失效
- 支持 Redis 或内存缓存

## 🔌 API 参考

### 身份验证端点

- `POST /api/v1/auth/register` - 注册新用户
- `POST /api/v1/auth/login` - 身份验证并接收 JWT 令牌
- `POST /api/v1/auth/logout` - 注销并使会话无效

### 聊天端点

- `POST /api/v1/chatbot/chat` - 发送消息并接收响应
- `POST /api/v1/chatbot/chat/stream` - 发送消息并获取流式响应
- `GET /api/v1/chatbot/history` - 获取对话历史
- `DELETE /api/v1/chatbot/history` - 清除聊天历史

### 健康检查和监控

- `GET /health` - 健康检查，包含数据库状态
- `GET /metrics` - Prometheus 指标端点

有关详细的 API 文档，请在运行应用程序时访问 `/docs`（Swagger UI）或 `/redoc`（ReDoc）。

## 📚 项目结构

```
whatsapp-food-order/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py              # 身份验证端点
│   │       ├── chatbot.py           # 聊天端点
│   │       └── api.py               # API 路由聚合
│   ├── core/
│   │   ├── config.py                # 配置管理
│   │   ├── logging.py               # 日志设置
│   │   ├── metrics.py               # Prometheus 指标
│   │   ├── middleware.py            # 自定义中间件
│   │   ├── limiter.py               # 速率限制
│   │   ├── langgraph/
│   │   │   ├── graph.py             # LangGraph 代理
│   │   │   └── tools.py             # 代理工具
│   │   └── prompts/
│   │       ├── __init__.py          # 提示词加载器
│   │       └── system.md            # 系统提示词
│   ├── models/
│   │   ├── user.py                  # 用户模型
│   │   └── session.py               # 会话模型
│   ├── schemas/
│   │   ├── auth.py                  # 认证 schemas
│   │   ├── chat.py                  # 聊天 schemas
│   │   └── graph.py                 # 图状态 schemas
│   ├── services/
│   │   ├── database.py              # 数据库服务
│   │   └── llm.py                   # LLM 服务（带重试）
│   ├── utils/
│   │   ├── __init__.py
│   │   └── graph.py                 # 图工具函数
│   └── main.py                      # 应用程序入口点
├── evals/
│   ├── evaluator.py                 # 评估逻辑
│   ├── main.py                      # 评估 CLI
│   ├── metrics/
│   │   └── prompts/                 # 评估指标定义
│   └── reports/                     # 生成的评估报告
├── grafana/                         # Grafana 仪表板
├── prometheus/                      # Prometheus 配置
├── scripts/                         # 实用脚本
├── docker-compose.yml               # Docker Compose 配置
├── Dockerfile                       # 应用程序 Docker 镜像
├── Makefile                         # 开发命令
├── pyproject.toml                   # Python 依赖
├── schema.sql                       # 数据库模式
├── SECURITY.md                      # 安全策略
└── README.md                        # 本文件
```

## 🛡️ 安全性

有关安全问题，请查看我们的[安全策略](SECURITY.md)。

## 📄 许可证

该项目根据 [LICENSE](LICENSE) 文件中指定的条款获得许可。

## 🤝 贡献

欢迎贡献！请确保：

1. 代码遵循项目的编码标准
2. 所有测试通过
3. 新功能包含适当的测试
4. 文档已更新
5. 提交消息遵循常规提交格式

## 📞 支持

如有问题、疑问或贡献，请在项目仓库中提交 issue
