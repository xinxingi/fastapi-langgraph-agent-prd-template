# 快速开始：添加新业务模块

本指南展示如何在 5 分钟内添加一个新的业务模块。

---

## 步骤 1: 创建模块目录

```bash
mkdir -p app/business/my_module
```

---

## 步骤 2: 创建 `__init__.py`

```python
# app/business/my_module/__init__.py

"""
我的业务模块

这个模块提供 XXX 功能。
"""

from fastapi import APIRouter

from app.business.my_module.router import router as my_router

# 创建主路由
router = APIRouter()
router.include_router(my_router)

# 模块配置（可选，但推荐）
MODULE_CONFIG = {
    "prefix": "/my_module",           # API 路径前缀
    "tags": ["my_module"],            # Swagger 标签
    "enabled": True,                  # 是否启用
    "description": "我的业务模块",     # 模块描述
    "version": "1.0.0",               # 版本号
}

__all__ = ["router", "MODULE_CONFIG"]
```

---

## 步骤 3: 创建路由文件

```python
# app/business/my_module/router.py

"""
我的业务模块路由定义
"""

from typing import Dict

from fastapi import APIRouter, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.logging import logger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/hello")
@limiter.limit("10 per minute")
async def hello() -> Dict[str, str]:
    """
    Hello World 端点
    
    Returns:
        Dict[str, str]: 问候消息
    """
    logger.info("hello_endpoint_called", module="my_module")
    return {
        "message": "Hello from my module!",
        "status": "success"
    }


@router.post("/process")
@limiter.limit("5 per minute")
async def process_data(data: Dict) -> Dict:
    """
    处理数据端点
    
    Args:
        data: 输入数据
        
    Returns:
        Dict: 处理结果
    """
    try:
        logger.info(
            "process_data_called",
            module="my_module",
            data_keys=list(data.keys())
        )
        
        # 你的业务逻辑
        result = {"processed": True, "data": data}
        
        return result
        
    except Exception as e:
        logger.exception(
            "process_data_failed",
            module="my_module",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="处理失败"
        )
```

---

## 步骤 4: 创建数据模型（可选）

```python
# app/business/my_module/schemas.py

"""
我的业务模块数据模型
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    """处理请求模型"""
    
    data: Dict[str, Any] = Field(..., description="要处理的数据")
    options: Optional[Dict[str, Any]] = Field(None, description="处理选项")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": {"key": "value"},
                    "options": {"mode": "fast"}
                }
            ]
        }
    }


class ProcessResponse(BaseModel):
    """处理响应模型"""
    
    success: bool = Field(..., description="是否成功")
    result: Dict[str, Any] = Field(..., description="处理结果")
    message: Optional[str] = Field(None, description="消息")
```

使用 Pydantic 模型更新路由:

```python
# app/business/my_module/router.py (更新版)

from app.business.my_module.schemas import ProcessRequest, ProcessResponse

@router.post("/process", response_model=ProcessResponse)
@limiter.limit("5 per minute")
async def process_data(request: ProcessRequest) -> ProcessResponse:
    """处理数据端点"""
    try:
        logger.info("process_data_called", module="my_module")
        
        # 你的业务逻辑
        result = {"processed": True, "input": request.data}
        
        return ProcessResponse(
            success=True,
            result=result,
            message="处理成功"
        )
        
    except Exception as e:
        logger.exception("process_data_failed", module="my_module")
        raise HTTPException(status_code=500, detail="处理失败")
```

---

## 步骤 5: 创建服务层（可选，推荐）

```python
# app/business/my_module/service.py

"""
我的业务模块服务层
"""

from typing import Any, Dict

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.logging import logger


class MyModuleService:
    """我的业务模块服务"""
    
    def __init__(self):
        logger.info("my_module_service_initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理数据（带重试）
        
        Args:
            data: 输入数据
            
        Returns:
            Dict: 处理结果
        """
        logger.info("processing_data", data_size=len(data))
        
        try:
            # 你的业务逻辑
            result = {
                "processed": True,
                "data": data,
                "timestamp": "2026-02-03T15:00:00Z"
            }
            
            logger.info("processing_completed", success=True)
            return result
            
        except Exception as e:
            logger.exception("processing_failed", error=str(e))
            raise


# 全局服务实例
my_module_service = MyModuleService()
```

在路由中使用服务:

```python
# app/business/my_module/router.py (更新版)

from app.business.my_module.service import my_module_service

@router.post("/process", response_model=ProcessResponse)
@limiter.limit("5 per minute")
async def process_data(request: ProcessRequest) -> ProcessResponse:
    """处理数据端点"""
    try:
        result = await my_module_service.process(request.data)
        
        return ProcessResponse(
            success=True,
            result=result,
            message="处理成功"
        )
        
    except Exception as e:
        logger.exception("process_endpoint_failed")
        raise HTTPException(status_code=500, detail="处理失败")
```

---

## 步骤 6: 添加独立配置（可选）

```python
# app/business/my_module/config.py

"""
我的业务模块配置
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings

from app.core.logging import logger


class MyModuleConfig(BaseSettings):
   """我的业务模块配置"""

   # 使用模块前缀避免冲突
   MY_MODULE_API_KEY: str = "default-key"
   MY_MODULE_API_URL: str = "https://api.example.com"
   MY_MODULE_TIMEOUT: float = 30.0
   MY_MODULE_MAX_RETRIES: int = 3
   MY_MODULE_ENABLED: bool = True

   class Config:
      env_file = "../../.env.development"
      case_sensitive = True


# 全局配置实例
config = MyModuleConfig()

logger.info(
   "my_module_config_loaded",
   api_url=config.MY_MODULE_API_URL,
   timeout=config.MY_MODULE_TIMEOUT,
   enabled=config.MY_MODULE_ENABLED
)
```

创建环境变量示例:

```bash
# app/business/my_module/.env.example

# My Module Configuration
MY_MODULE_API_KEY=your-api-key-here
MY_MODULE_API_URL=https://api.example.com
MY_MODULE_TIMEOUT=30.0
MY_MODULE_MAX_RETRIES=3
MY_MODULE_ENABLED=true
```

---

## 步骤 7: 重启应用

```bash
uvicorn app.main:app --reload
```

---

## 步骤 8: 验证模块已注册

### 方法 1: 查看日志

```bash
# 你应该看到类似的日志:
[info] business_module_loaded
  module=my_module
  enabled=True
  prefix=/my_module

[info] business_module_registered
  module=my_module
  prefix=/my_module
  tags=['my_module']
```

### 方法 2: 访问 API 文档

打开浏览器访问: http://localhost:8000/docs

你会看到新的端点:
- `GET /api/v1/my_module/hello`
- `POST /api/v1/my_module/process`

### 方法 3: 测试端点

```bash
# 测试 hello 端点
curl http://localhost:8000/api/v1/my_module/hello

# 预期响应:
{
  "message": "Hello from my module!",
  "status": "success"
}

# 测试 process 端点
curl -X POST http://localhost:8000/api/v1/my_module/process \
  -H "Content-Type: application/json" \
  -d '{"data": {"key": "value"}}'
```

---

## 完整的文件结构

```
app/business/my_module/
├── __init__.py          # 模块入口（必需）
├── router.py            # 路由定义
├── schemas.py           # Pydantic 数据模型（推荐）
├── service.py           # 业务逻辑服务（推荐）
├── config.py            # 独立配置（可选）
├── .env.example         # 环境变量示例（可选）
├── README.md            # 模块文档（推荐）
└── tests/               # 单元测试（推荐）
    ├── __init__.py
    └── test_router.py
```

---

## 最佳实践

### 1. 遵循项目规范

参考 `AGENTS.md` 中的规范:
- 使用 `structlog` 进行日志记录
- 使用 `tenacity` 实现重试
- 使用 `slowapi` 添加速率限制
- 所有异步操作使用 `async/await`
- 使用 Pydantic v2 进行数据验证

### 2. 日志记录规范

```python
# ✅ 正确 - 使用 lowercase_with_underscores，变量作为 kwargs
logger.info("user_action_completed", user_id=user_id, action="create")

# ❌ 错误 - 使用 f-string
logger.info(f"User {user_id} completed action")

# ✅ 正确 - 异常使用 logger.exception
try:
    process_data()
except Exception as e:
    logger.exception("process_failed", details=str(e))
```

### 3. 错误处理

```python
# 使用 early return 和守卫子句
@router.post("/process")
async def process_data(data: Dict):
    # 验证输入
    if not data:
        logger.warning("empty_data_received")
        raise HTTPException(status_code=400, detail="数据不能为空")
    
    if "required_field" not in data:
        logger.warning("missing_required_field")
        raise HTTPException(status_code=400, detail="缺少必需字段")
    
    # 成功路径放最后
    try:
        result = await process(data)
        return result
    except Exception as e:
        logger.exception("processing_error")
        raise HTTPException(status_code=500, detail="处理失败")
```

### 4. 速率限制

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/expensive-operation")
@limiter.limit("5 per minute")  # 限制每分钟 5 次
async def expensive_operation():
    pass
```

### 5. 类型提示

```python
# ✅ 完整的类型提示
async def process_data(
    data: Dict[str, Any],
    user_id: Optional[int] = None
) -> ProcessResponse:
    pass

# ❌ 缺少类型提示
async def process_data(data, user_id=None):
    pass
```

---

## 常见问题

### Q: 模块没有被注册？

**A:** 检查:
1. `__init__.py` 是否存在
2. 是否导出了 `router`
3. 查看启动日志中是否有错误信息
4. 确保模块目录在 `app/business/` 下

### Q: 如何禁用某个模块？

**A:** 在 `MODULE_CONFIG` 中设置:
```python
MODULE_CONFIG = {
    "enabled": False,  # 禁用模块
    # ... 其他配置
}
```

### Q: 如何添加模块依赖？

**A:** 在 `__init__.py` 中导入依赖:
```python
from app.business.other_module.service import other_service

# 在路由或服务中使用
```

### Q: 如何添加认证？

**A:** 使用框架提供的依赖:
```python
from app.api.dependencies import get_current_session

@router.get("/protected")
async def protected_endpoint(session = Depends(get_current_session)):
    # 只有认证用户可以访问
    return {"user_id": session.user_id}
```

---

## 下一步

1. **阅读完整文档**:
   - `ARCHITECTURE_EVOLUTION.md` - 架构演进
   - `MIGRATION_SUMMARY.md` - 迁移总结
   - `app/core/BUSINESS_REGISTRY.md` - 注册系统详解

2. **查看示例**:
   - `app/business/example_module/` - 简单示例
   - `app/business/hr_onboarding_verification/` - 完整示例

3. **添加测试**:
   ```python
   # app/business/my_module/tests/test_router.py
   
   import pytest
   from fastapi.testclient import TestClient
   
   def test_hello_endpoint(client: TestClient):
       response = client.get("/api/v1/my_module/hello")
       assert response.status_code == 200
       assert response.json()["status"] == "success"
   ```

---

## 🎉 恭喜！

你已经成功添加了一个新的业务模块！

**记住**: 添加新模块无需修改任何框架代码，只需创建目录和实现业务逻辑即可！

有问题？查看项目文档或提出 issue。
