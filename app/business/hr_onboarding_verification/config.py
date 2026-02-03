"""HR入职文件质量核验业务配置。

此模块包含HR入职文件质量核验业务的配置设置。
所有配置从环境变量读取，与框架配置独立。
"""

import os


class HRVerificationConfig:
    """HR入职文件质量核验配置类。

    从环境变量读取配置，提供默认值。
    """

    def __init__(self):
        """初始化HR核验配置。"""
        # API配置
        self.BASE_URL = os.getenv("HR_VERIFICATION_BASE_URL", "https://data-sit.ysservice.com.cn/api")
        self.API_KEY = os.getenv("HR_VERIFICATION_API_KEY", "sk-7XnQ9vW2kL5mZ8pA3rJ6tY1cB4dF0gH9jK2xV5nB8mQ1wE")
        self.TIMEOUT = float(os.getenv("HR_VERIFICATION_TIMEOUT", "30.0"))

        # 速率限制
        self.RATE_LIMIT = os.getenv("HR_VERIFICATION_RATE_LIMIT", "20 per minute")

        # 重试配置
        self.MAX_RETRIES = int(os.getenv("HR_VERIFICATION_MAX_RETRIES", "3"))
        self.RETRY_MIN_WAIT = int(os.getenv("HR_VERIFICATION_RETRY_MIN_WAIT", "4"))
        self.RETRY_MAX_WAIT = int(os.getenv("HR_VERIFICATION_RETRY_MAX_WAIT", "10"))


# 创建全局配置实例
hr_config = HRVerificationConfig()
