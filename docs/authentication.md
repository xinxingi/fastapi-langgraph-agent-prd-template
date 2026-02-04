# 用户认证 API 使用指南

本项目实现了双重认证机制：
- **JWT Token** - 用于用户会话管理（短期，30天）
- **API Key** - 用于程序调用（长期，最长可设置到 2099 年，格式为 `sk-xxx`）

**重要说明**：两种 Token 都使用 **Bearer 认证方案**（RFC 6750）通过 HTTP 头传输：
```
Authorization: Bearer <token>
```
- "Bearer" 是 HTTP 认证方法，不是 Token 类型
- JWT Token 和 API Key 都使用相同的 Bearer 头格式传输

---

## 认证流程说明

### 1. 用户注册
注册新用户账号，**不返回 token**，需要单独登录。

### 2. 用户登录
登录获得 **JWT Token**，用于后续 API 调用和会话管理。

### 3. 创建 API Key（可选）
登录后，用户可以主动创建 **API Key**，用于程序/脚本调用。
有效期可以从 1 天到 2099 年 12 月 31 日之间任意设置。
API Key 格式为 `sk-xxx`，使用时通过 Bearer 认证方案传输。

---

## API 端点详细说明

### 1. 注册用户

**请求:**
```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**cURL 示例:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**成功响应:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "message": "User registered successfully"
}
```

**密码要求:**
- ✅ 至少 8 个字符
- ✅ 至少 1 个大写字母
- ✅ 至少 1 个小写字母
- ✅ 至少 1 个数字
- ✅ 至少 1 个特殊字符 (!@#$%^&*(),.?":{}|<>)

---

### 2. 用户登录（获取 JWT Token）

**请求:**
```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com
password=SecurePass123!
grant_type=password
```

**cURL 示例:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePass123!&grant_type=password"
```

**成功响应:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2026-03-05T10:56:00.000000Z"
}
```

**Token 说明:**
- **access_token**: JWT Token 字符串
- **token_type**: 始终为 "bearer"
- **expires_at**: 过期时间（默认 30 天）

---

### 3. 使用 JWT Token 访问受保护的 API

在请求头中添加 `Authorization: Bearer <jwt_token>`

**示例:**
```bash
curl -X GET "http://localhost:8000/api/v1/chatbot/sessions" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 4. 创建 API Key

登录后，可以创建长期有效的 API Key（格式为 `sk-xxx`），用于程序调用。

**请求:**
```bash
POST /api/v1/auth/tokens
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "name": "My API Key",
  "expires_in_days": 90
}
```

**cURL 示例:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/tokens" \
  -H "Authorization: Bearer <你的JWT Token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Script API Key",
    "expires_in_days": 90
  }'

# 创建长期有效的 API Key (例如 10 年)
curl -X POST "http://localhost:8000/api/v1/auth/tokens" \
  -H "Authorization: Bearer <你的JWT Token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Long-term API Key",
    "expires_in_days": 3650
  }'
```

**成功响应:**
```json
{
  "id": 1,
  "name": "My API Key",
  "token": "sk-k_1aotxH_JsxJPnqkDPz2-Y4dyZOXiLC9wW010Fbnlc",
  "expires_at": "2026-05-04T10:51:33.537086Z",
  "created_at": "2026-02-03T10:51:33.537086Z"
}
```

**⚠️ 重要提示:**
- API Key **仅在创建时返回一次**，请妥善保存
- 如果丢失，需要撤销旧的并创建新的

---

### 5. 使用 API Key 访问 API

API Key 的格式为 `sk-xxx`，使用方式与 JWT Token 相同：

**示例:**
```bash
curl -X GET "http://localhost:8000/api/v1/chatbot/sessions" \
  -H "Authorization: Bearer sk-k_1aotxH_JsxJPnqkDPz2-Y4dyZOXiLC9wW010Fbnlc"
```

---

### 6. 撤销 API Key

**请求:**
```bash
DELETE /api/v1/auth/tokens/{token_id}
Authorization: Bearer <jwt_token or api_key>
```

**cURL 示例:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/auth/tokens/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**成功响应:**
```json
{
  "message": "Token revoked successfully"
}
```

---

## 两种 Token 的区别

| 特性 | JWT Token | API Key |
|------|-----------|---------|
| **获取方式** | 登录自动获得 | 用户主动创建 |
| **格式** | JWT 标准格式 | `sk-xxx` 格式 |
| **传输方式** | `Authorization: Bearer <jwt>` | `Authorization: Bearer <api_key>` |
| **有效期** | 30 天（配置） | 1 天 ~ 2099 年（创建时指定） |
| **用途** | 用户会话管理、Web 应用 | 程序调用、脚本、第三方集成 |
| **存储** | 客户端（LocalStorage/Cookie） | 服务器数据库 |
| **撤销** | 到期自动失效 | 可以手动撤销 |
| **管理** | 无需管理 | 可以创建多个、查看列表、撤销 |

**说明**：Bearer 是 HTTP 认证方案（RFC 6750），不是 Token 类型。两种 Token 都通过 Bearer 头传输。

---

## 完整使用示例

### Python 脚本示例

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. 注册
register_response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "user@example.com",
        "password": "SecurePass123!"
    }
)
print("注册:", register_response.json())

# 2. 登录获取 JWT
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "user@example.com",
        "password": "SecurePass123!",
        "grant_type": "password"
    }
)
jwt_token = login_response.json()["access_token"]
print("JWT Token:", jwt_token[:50] + "...")

# 3. 使用 JWT 访问 API
headers = {"Authorization": f"Bearer {jwt_token}"}
sessions = requests.get(f"{BASE_URL}/chatbot/sessions", headers=headers)
print("Sessions:", sessions.json())

# 4. 创建 API Key (示例：90天有效期)
api_key_response = requests.post(
    f"{BASE_URL}/auth/tokens",
    headers=headers,
    json={
        "name": "My Script API Key",
        "expires_in_days": 90  # 可以设置 1 ~ 27000 天（最长到2099年）
    }
)
api_key = api_key_response.json()["token"]
print("API Key:", api_key)

# 5. 使用 API Key 访问（无需重新登录）
api_headers = {"Authorization": f"Bearer {api_key}"}
sessions = requests.get(f"{BASE_URL}/chatbot/sessions", headers=api_headers)
print("Sessions with API Key:", sessions.json())
```

---

## 错误处理

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```
**原因**: Token 无效、过期或已撤销

### 422 Unprocessable Entity
```json
{
  "detail": "密码必须包含至少一个大写字母"
}
```
**原因**: 输入验证失败

### 400 Bad Request
```json
{
  "detail": "Email already registered"
}
```
**原因**: 邮箱已被注册

---

## 配置说明

在 `.env.development` 中配置 JWT 参数：

```env
# JWT 配置
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_DAYS=30
```

**⚠️ 生产环境安全提示:**
- 使用强随机字符串作为 `JWT_SECRET_KEY`
- 定期轮换密钥
- 使用 HTTPS 传输所有 Token
- 不要在日志中记录完整的 Token

---

## 总结

1. **用户注册** → 只返回成功消息
2. **用户登录** → 返回 JWT Token（30天）
3. **日常使用** → 使用 JWT Token 访问 API（Bearer 头传输）
4. **程序调用** → 创建 API Key（最长到2099年，Bearer 头传输）
5. **安全管理** → 可以随时撤销 API Key

**关键概念**：
- **Bearer** = HTTP 认证方案（RFC 6750），不是 Token 类型
- **JWT Token** = 短期会话凭证，通过 Bearer 头传输
- **API Key** = 长期 API 凭证（`sk-xxx` 格式），通过 Bearer 头传输

这种设计既保证了用户会话的灵活性（JWT），又提供了程序调用的便利性（API Key）。
