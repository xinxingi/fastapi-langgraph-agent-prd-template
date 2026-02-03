"""业务模块自动发现和注册工具。

此模块提供自动扫描 app/business 目录下的所有业务模块，
并自动注册它们的路由到主路由器。

业务模块规范：
1. 业务模块必须在 app/business 目录下
2. 业务模块必须有 __init__.py 文件
3. 在 __init__.py 中暴露路由器和配置：
   - router: APIRouter 实例（必需）
   - MODULE_CONFIG: dict 配置（可选）

示例：
    # app/business/my_module/__init__.py
    from fastapi import APIRouter

    router = APIRouter()
    # ... 注册路由

    MODULE_CONFIG = {
        "prefix": "/my_module",
        "tags": ["my_module"],
        "enabled": True,
    }

    __all__ = ["router", "MODULE_CONFIG"]
"""

import importlib
import os
from pathlib import Path
from typing import Dict, List, Tuple

from fastapi import APIRouter

from app.core.logging import logger


class BusinessModuleRegistry:
    """业务模块注册表。

    自动发现和注册 app/business 目录下的所有业务模块。
    """

    def __init__(self, business_dir: str = "app/business"):
        """初始化业务模块注册表。

        Args:
            business_dir: 业务模块目录路径
        """
        self.business_dir = business_dir
        self.registered_modules: Dict[str, dict] = {}

    def discover_modules(self) -> List[str]:
        """发现所有业务模块。

        Returns:
            业务模块名称列表
        """
        business_path = Path(self.business_dir)

        if not business_path.exists():
            logger.warning(
                "business_directory_not_found",
                path=str(business_path),
            )
            return []

        modules = []
        for item in business_path.iterdir():
            # 跳过非目录和私有目录
            if not item.is_dir() or item.name.startswith("_"):
                continue

            # 检查是否有 __init__.py
            init_file = item / "__init__.py"
            if init_file.exists():
                modules.append(item.name)
                logger.debug(
                    "business_module_discovered",
                    module=item.name,
                )

        logger.info(
            "business_modules_discovery_completed",
            total_count=len(modules),
            modules=modules,
        )

        return modules

    def load_module(self, module_name: str) -> Tuple[APIRouter, dict]:
        """加载业务模块。

        Args:
            module_name: 模块名称

        Returns:
            (router, config) 元组

        Raises:
            ImportError: 模块导入失败
            AttributeError: 模块缺少必需的属性
        """
        module_path = f"app.business.{module_name}"

        try:
            module = importlib.import_module(module_path)

            # 获取路由器（必需）
            if not hasattr(module, "router"):
                raise AttributeError(f"模块 {module_name} 缺少 'router' 属性")

            router = getattr(module, "router")

            if not isinstance(router, APIRouter):
                raise TypeError(f"模块 {module_name} 的 'router' 必须是 APIRouter 实例")

            # 获取配置（可选）
            default_config = {
                "prefix": f"/{module_name}",
                "tags": [module_name],
                "enabled": True,
            }

            if hasattr(module, "MODULE_CONFIG"):
                config = getattr(module, "MODULE_CONFIG")
                # 合并默认配置和模块配置
                default_config.update(config)

            logger.info(
                "business_module_loaded",
                module=module_name,
                prefix=default_config.get("prefix"),
                enabled=default_config.get("enabled"),
            )

            return router, default_config

        except Exception as e:
            logger.exception(
                "business_module_load_failed",
                module=module_name,
                error=str(e),
            )
            raise

    def register_module(
        self,
        api_router: APIRouter,
        module_name: str,
        force: bool = False,
    ) -> bool:
        """注册单个业务模块。

        Args:
            api_router: 主API路由器
            module_name: 模块名称
            force: 是否强制注册（忽略 enabled 配置）

        Returns:
            是否成功注册
        """
        try:
            router, config = self.load_module(module_name)

            # 检查是否启用
            if not force and not config.get("enabled", True):
                logger.info(
                    "business_module_skipped",
                    module=module_name,
                    reason="disabled_in_config",
                )
                return False

            # 注册路由
            api_router.include_router(
                router,
                prefix=config.get("prefix", f"/{module_name}"),
                tags=config.get("tags", [module_name]),
            )

            # 记录已注册的模块
            self.registered_modules[module_name] = config

            logger.info(
                "business_module_registered",
                module=module_name,
                prefix=config.get("prefix"),
                tags=config.get("tags"),
            )

            return True

        except Exception as e:
            logger.exception(
                "business_module_registration_failed",
                module=module_name,
                error=str(e),
            )
            return False

    def register_all(
        self,
        api_router: APIRouter,
        exclude: List[str] = None,
    ) -> Dict[str, bool]:
        """自动发现并注册所有业务模块。

        Args:
            api_router: 主API路由器
            exclude: 要排除的模块名称列表

        Returns:
            {模块名: 是否成功注册} 字典
        """
        exclude = exclude or []
        modules = self.discover_modules()
        results = {}

        for module_name in modules:
            if module_name in exclude:
                logger.info(
                    "business_module_excluded",
                    module=module_name,
                )
                results[module_name] = False
                continue

            success = self.register_module(api_router, module_name)
            results[module_name] = success

        # 统计
        total = len(results)
        successful = sum(1 for v in results.values() if v)
        failed = total - successful

        logger.info(
            "business_modules_registration_completed",
            total=total,
            successful=successful,
            failed=failed,
            registered_modules=list(self.registered_modules.keys()),
        )

        return results

    def get_registered_modules(self) -> Dict[str, dict]:
        """获取已注册的模块信息。

        Returns:
            {模块名: 配置} 字典
        """
        return self.registered_modules.copy()


# 创建全局注册表实例
registry = BusinessModuleRegistry()


def auto_register_business_modules(
    api_router: APIRouter,
    exclude: List[str] = None,
) -> Dict[str, bool]:
    """自动注册所有业务模块的便捷函数。

    Args:
        api_router: 主API路由器
        exclude: 要排除的模块名称列表

    Returns:
        {模块名: 是否成功注册} 字典
    """
    return registry.register_all(api_router, exclude=exclude)
