"""应用程序的速率限制配置。

该模块使用slowapi配置速率限制，默认限制在
应用程序设置中定义。速率限制基于远程IP地址应用。
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# 初始化速率限制器
limiter = Limiter(key_func=get_remote_address, default_limits=settings.RATE_LIMIT_DEFAULT)
