"""此文件包含应用程序的图工具。"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.messages import trim_messages as _trim_messages

from app.core.config import settings
from app.core.logging import logger
from app.schemas import Message


def dump_messages(messages: list[Message]) -> list[dict]:
    """将消息转储为字典列表。

    Args:
        messages (list[Message]): 要转储的消息。

    Returns:
        list[dict]: 转储后的消息。
    """
    return [message.model_dump() for message in messages]


def process_llm_response(response: BaseMessage) -> BaseMessage:
    """处理LLM响应以处理结构化内容块（例如，来自GPT-5模型）。

    GPT-5模型以如下格式返回内容块列表：
    [
        {'id': '...', 'summary': [], 'type': 'reasoning'},
        {'type': 'text', 'text': 'actual response'}
    ]

    此函数从这种结构中提取实际的文本内容。

    Args:
        response: LLM的原始响应

    Returns:
        处理后内容的BaseMessage
    """
    if isinstance(response.content, list):
        # 从内容块中提取文本
        text_parts = []
        for block in response.content:
            if isinstance(block, dict):
                # 处理文本块
                if block.get("type") == "text" and "text" in block:
                    text_parts.append(block["text"])
                # 记录推理块以供调试
                elif block.get("type") == "reasoning":
                    logger.debug(
                        "reasoning_block_received",
                        reasoning_id=block.get("id"),
                        has_summary=bool(block.get("summary")),
                    )
            elif isinstance(block, str):
                text_parts.append(block)

        # 连接所有文本部分
        response.content = "".join(text_parts)
        logger.debug(
            "processed_structured_content",
            block_count=len(response.content) if isinstance(response.content, list) else 1,
            extracted_length=len(response.content) if isinstance(response.content, str) else 0,
        )

    return response


def prepare_messages(messages: list[Message], llm: BaseChatModel, system_prompt: str) -> list[Message]:
    """为LLM准备消息。

    Args:
        messages (list[Message]): 要准备的消息。
        llm (BaseChatModel): 要使用的LLM。
        system_prompt (str): 要使用的系统提示词。

    Returns:
        list[Message]: 准备好的消息。
    """
    try:
        trimmed_messages = _trim_messages(
            dump_messages(messages),
            strategy="last",
            token_counter=llm,
            max_tokens=settings.MAX_TOKENS,
            start_on="human",
            include_system=False,
            allow_partial=False,
        )
    except ValueError as e:
        # 处理无法识别的内容块（例如，来自GPT-5的推理块）
        if "Unrecognized content block type" in str(e):
            logger.warning(
                "token_counting_failed_skipping_trim",
                error=str(e),
                message_count=len(messages),
            )
            # 跳过修剪并返回所有消息
            trimmed_messages = messages
        else:
            raise

    return [Message(role="system", content=system_prompt)] + trimmed_messages
