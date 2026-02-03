"""此文件包含应用程序的清理工具。"""

import html
import re
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)


def sanitize_string(value: str) -> str:
    """清理字符串以防止XSS和其他注入攻击。

    Args:
        value: 要清理的字符串

    Returns:
        str: 清理后的字符串
    """
    # 如果不是字符串则转换为字符串
    if not isinstance(value, str):
        value = str(value)

    # HTML转义以防止XSS
    value = html.escape(value)

    # 移除可能被转义的script标签
    value = re.sub(r"&lt;script.*?&gt;.*?&lt;/script&gt;", "", value, flags=re.DOTALL)

    # 移除空字节
    value = value.replace("\0", "")

    return value


def sanitize_email(email: str) -> str:
    """清理电子邮件地址。

    Args:
        email: 要清理的电子邮件地址

    Returns:
        str: 清理后的电子邮件地址
    """
    # 基本清理
    email = sanitize_string(email)

    # 确保电子邮件格式（简单检查）
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        raise ValueError("无效的电子邮件格式")

    return email.lower()


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """递归清理字典中的所有字符串值。

    Args:
        data: 要清理的字典

    Returns:
        Dict[str, Any]: 清理后的字典
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = sanitize_list(value)
        else:
            sanitized[key] = value
    return sanitized


def sanitize_list(data: List[Any]) -> List[Any]:
    """递归清理列表中的所有字符串值。

    Args:
        data: 要清理的列表

    Returns:
        List[Any]: 清理后的列表
    """
    sanitized = []
    for item in data:
        if isinstance(item, str):
            sanitized.append(sanitize_string(item))
        elif isinstance(item, dict):
            sanitized.append(sanitize_dict(item))
        elif isinstance(item, list):
            sanitized.append(sanitize_list(item))
        else:
            sanitized.append(item)
    return sanitized


def validate_password_strength(password: str) -> bool:
    """验证密码强度。

    Args:
        password: 要验证的密码

    Returns:
        bool: 密码是否足够强

    Raises:
        ValueError: 如果密码不够强及原因
    """
    if len(password) < 8:
        raise ValueError("密码长度至少为8个字符")

    if not re.search(r"[A-Z]", password):
        raise ValueError("密码必须包含至少一个大写字母")

    if not re.search(r"[a-z]", password):
        raise ValueError("密码必须包含至少一个小写字母")

    if not re.search(r"[0-9]", password):
        raise ValueError("密码必须包含至少一个数字")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("密码必须包含至少一个特殊字符")

    return True
