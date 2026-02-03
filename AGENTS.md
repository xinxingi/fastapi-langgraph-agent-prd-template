# AI Agent 开发指南

本文档为在此 LangGraph FastAPI Agent 项目中工作的 AI 代理提供了基本指南。

## 项目概述

这是一个生产就绪的 AI 代理应用程序，构建于：
- **LangGraph** - 用于有状态的、多步骤的 AI 代理工作流
- **FastAPI** - 用于高性能异步 REST API 端点
- **Langfuse** - 用于 LLM 可观测性和跟踪
- **PostgreSQL + pgvector** - 用于长期记忆存储（mem0ai）
- **JWT 身份验证** - 带有会话管理
- **Prometheus + Grafana** - 用于监控

## 快速参考：关键规则

### 导入规则
- **所有导入必须在文件顶部** - 永远不要在函数或类内部添加导入

### 日志规则
- 所有日志都使用 **structlog**
- 日志消息必须使用 **lowercase_with_underscores** 格式（例如，`"user_login_successful"`）
- **在 structlog 事件中不使用 f-字符串** - 将变量作为 kwargs 传递
- 使用 `logger.exception()` 而不是 `logger.error()` 来保留回溯信息
- 示例：`logger.info("chat_request_received", session_id=session.id, message_count=len(messages))`

### 重试规则
- **始终使用 tenacity 库** 进行重试逻辑
- 配置指数退避
- 示例：`@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))`

### 输出规则
- **始终启用 rich 库** 进行格式化的控制台输出
- 使用 rich 来显示进度条、表格、面板和格式化文本

### 缓存规则
- **仅缓存成功响应**，永远不缓存错误
- 根据数据波动性使用适当的缓存 TTL

### FastAPI 规则
- 所有路由必须有速率限制装饰器
- 使用依赖注入来处理服务、数据库连接和认证
- 所有数据库操作必须是异步的

## 代码风格约定

### Python/FastAPI
- 对异步操作使用 `async def`
- 为所有函数签名使用类型提示
- 优先使用 Pydantic 模型而不是原始字典
- 使用函数式、声明式编程；除服务和代理外避免使用类
- 文件命名：小写加下划线（例如，`user_routes.py`）
- 使用 RORO 模式（接收一个对象，返回一个对象）

### 错误处理
- 在函数开头处理错误
- 对错误条件使用早期返回
- 将成功路径放在函数最后
- 使用守卫子句处理前置条件
- 对预期错误使用 `HTTPException` 并设置适当的状态码

## LangGraph 和 LangChain 模式

### 图结构
- 使用 `StateGraph` 构建 AI 代理工作流
- 使用 Pydantic 模型定义清晰的状态模式（参见 `app/schemas/graph.py`）
- 对生产工作流使用 `CompiledStateGraph`
- 实现 `AsyncPostgresSaver` 进行检查点和持久化
- 使用 `Command` 控制节点之间的图流

### 跟踪
- 使用 Langfuse 的 LangChain `CallbackHandler` 跟踪所有 LLM 调用
- 所有 LLM 操作必须启用 Langfuse 跟踪

### 记忆（mem0ai）
- 使用 `AsyncMemory` 进行语义记忆存储
- 为每个用户 ID 存储记忆，以获得个性化体验
- 使用异步方法：`add()`、`get()`、`search()`、`delete()`

## 身份验证和安全性

- 使用 JWT 令牌进行身份验证
- 实现基于会话的用户管理（参见 `app/api/v1/auth.py`）
- 对受保护端点使用 `get_current_session` 依赖
- 将敏感数据存储在环境变量中
- 使用 Pydantic 模型验证所有用户输入

## 数据库操作

- 使用 SQLModel 作为 ORM 模型（结合了 SQLAlchemy + Pydantic）
- 在 `app/models/` 目录中定义模型
- 使用 asyncpg 进行异步数据库操作
- 使用 LangGraph 的 AsyncPostgresSaver 进行代理检查点

## 性能指南

- 最小化阻塞 I/O 操作
- 对所有数据库和外部 API 调用使用异步
- 对频繁访问的数据实现缓存
- 对数据库连接使用连接池
- 通过流式响应优化 LLM 调用

## 可观测性

- 在所有代理操作上集成 Langfuse 进行 LLM 跟踪
- 导出 Prometheus 指标用于 API 性能监控
- 使用带有上下文绑定的结构化日志记录（request_id、session_id、user_id）
- 跟踪 LLM 推理持续时间、令牌使用量和成本

## 测试和评估

- 为 LLM 输出实现基于指标的评估（参见 `evals/` 目录）
- 在 `evals/metrics/prompts/` 中将自定义评估指标创建为 markdown 文件
- 使用 Langfuse 跟踪作为评估数据源
- 生成带有成功率的 JSON 报告

## 配置管理

- 使用环境特定的配置文件（`.env.development`、`.env.staging`、`.env.production`）
- 使用 Pydantic Settings 进行类型安全的配置（参见 `app/core/config.py`）
- 永远不要硬编码秘密或 API 密钥

## 关键依赖

- **FastAPI** - Web 框架
- **LangGraph** - 代理工作流编排
- **LangChain** - LLM 抽象和工具
- **Langfuse** - LLM 可观测性和跟踪
- **Pydantic v2** - 数据验证和设置
- **structlog** - 结构化日志
- **mem0ai** - 长期记忆管理
- **PostgreSQL + pgvector** - 数据库和向量存储
- **SQLModel** - 数据库模型的 ORM
- **tenacity** - 重试逻辑
- **rich** - 终端格式化
- **slowapi** - 速率限制
- **prometheus-client** - 指标收集

## 本项目的 10 条戒律

1. 所有路由必须有速率限制装饰器
2. 所有 LLM 操作必须有 Langfuse 跟踪
3. 所有异步操作必须有适当的错误处理
4. 所有日志必须遵循结构化日志格式，事件名称使用 lowercase_underscore
5. 所有重试必须使用 tenacity 库
6. 所有控制台输出应使用 rich 格式化
7. 所有缓存应仅存储成功响应
8. 所有导入必须在文件顶部
9. 所有数据库操作必须是异步的
10. 所有端点必须有适当的类型提示和 Pydantic 模型

## 常见陷阱要避免

- ❌ 在 structlog 事件中使用 f-字符串
- ❌ 在函数内部添加导入
- ❌ 忘记在路由上添加速率限制装饰器
- ❌ 在 LLM 调用上缺少 Langfuse 跟踪
- ❌ 缓存错误响应
- ❌ 对异常使用 `logger.error()` 而不是 `logger.exception()`
- ❌ 阻塞 I/O 操作而不使用异步
- ❌ 硬编码秘密或 API 密钥
- ❌ 函数签名上缺少类型提示

## 进行更改时

在修改代码之前：
1. 首先阅读现有实现
2. 检查代码库中的相关模式
3. 确保与现有代码风格一致
4. 添加具有结构化格式的适当日志记录
5. 包含带有早期返回的错误处理
6. 添加类型提示和 Pydantic 模型
7. 验证 LLM 调用已启用 Langfuse 跟踪

## 参考资料

- LangGraph 文档：https://langchain-ai.github.io/langgraph/
- LangChain 文档：https://python.langchain.com/docs/
- FastAPI 文档：https://fastapi.tiangolo.com/
- Langfuse 文档：https://langfuse.com/docs
