"""框架层服务模块。

此模块包含可复用的框架服务。
"""

from app.core.services.llm import LLMRegistry, LLMService

__all__ = ["LLMRegistry", "LLMService"]
