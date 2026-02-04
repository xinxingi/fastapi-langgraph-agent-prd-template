# 问题排查指南

## 问题：登录后显示 "Network Error" 和 "加载 API Key 列表失败"

### 原因

在最新的更新中，我们为 API Key 表添加了新字段 `last_used_at`。如果您的数据库表结构还是旧版本，就会导致查询失败。

### 症状

- 登录成功，显示"登录成功"消息
- 跳转到 `/tokens` 页面后出现错误：
  - ❌ "Network Error"
  - ❌ "加载 API Key 列表失败"
- 控制台可能显示数据库相关错误

### 解决方案

您有以下几种选择：

#### 方法 1：自动迁移（推荐）⭐

运行 Python 迁移脚本：

```bash
uv run python migrate_add_last_used_at.py
```

脚本会自动：
- ✓ 检测表名（`bs_api_keys` 或 `bs_bearer_tokens`）
- ✓ 检查字段是否已存在
- ✓ 添加 `last_used_at` 字段
- ✓ 验证迁移成功

#### 方法 2：手动 SQL 迁移

如果您更喜欢手动操作，可以执行 SQL：

```bash
psql -U postgres -d your_database_name -f add_last_used_at_field.sql
```

或者直接在 PostgreSQL 中执行：

```sql
-- 添加字段
ALTER TABLE bs_api_keys ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP NULL;

-- 或者如果表名是旧版本
ALTER TABLE bs_bearer_tokens ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP NULL;
```

#### 方法 3：重建表（仅开发环境，会清空数据）⚠️

**警告：此方法会删除所有用户和 API Key 数据！**

```sql
DROP TABLE bs_api_keys CASCADE;
DROP TABLE bs_users CASCADE;
```

然后重启后端，SQLModel 会自动创建新表结构：

```bash
make dev
```

### 验证修复

迁移完成后：

1. 重启后端：`make dev`
2. 重启前端：`cd frontend && npm run dev`
3. 清除浏览器缓存或使用无痕模式
4. 登录并访问 `/tokens` 页面
5. 应该能正常看到 API Key 列表，包含新增的"最后使用"列

### 新功能说明

迁移后您将获得以下新功能：

- ✨ **最后使用时间**：显示每个 API Key 最后一次被使用的时间
- ✨ **剩余时间**：人性化显示 API Key 还有多久过期
- ✨ **分页支持**：支持 10/20/50/100 条/页
- ✨ **搜索和筛选**：按名称搜索，按状态筛选（全部/有效/已过期/已撤销）

## 其他常见问题

### 问题：后端未运行

**症状**：前端显示 "Network Error"

**解决**：
```bash
make dev
```

### 问题：前端端口冲突

**症状**：前端启动时显示 "Port 3000 is in use"

**解决**：
- 前端会自动使用其他端口（如 3001）
- 访问终端中显示的实际端口
- 或手动停止占用 3000 端口的进程：
  ```bash
  lsof -ti:3000 | xargs kill -9
  ```

### 问题：错误消息显示为英文

**症状**：看到 "Incorrect email or password" 而不是中文

**解决**：
- 确保使用最新代码（commit `785d351` 或之后）
- 重启后端：`make dev`

### 问题：登录/注册错误消息一闪而过

**症状**：错误消息显示后立即消失

**解决**：
- 已在 commit `5a212a4` 中修复
- 现在使用 ElMessage 顶部弹窗，持续 5 秒
- 可手动关闭

## 需要帮助？

如果以上方法都无法解决您的问题，请检查：

1. 后端日志：查看终端输出是否有错误
2. 前端控制台：打开浏览器开发者工具查看错误
3. 数据库连接：确认 PostgreSQL 正在运行
4. 环境变量：检查 `.env.development` 配置是否正确

提交 Issue 时请附上：
- 错误截图
- 后端日志
- 前端控制台错误
- 您尝试的解决方法
