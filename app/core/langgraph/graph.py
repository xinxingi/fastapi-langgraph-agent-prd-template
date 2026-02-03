"""此文件包含 LangGraph Agent/工作流以及与 LLM 的交互。"""

import asyncio
from typing import (
    AsyncGenerator,
    Optional,
)
from urllib.parse import quote_plus

from asgiref.sync import sync_to_async
from langchain_core.messages import (
    BaseMessage,
    ToolMessage,
    convert_to_openai_messages,
)
from langfuse.langchain import CallbackHandler
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import (
    END,
    StateGraph,
)
from langgraph.graph.state import (
    Command,
    CompiledStateGraph,
)
from langgraph.types import (
    RunnableConfig,
    StateSnapshot,
)
from mem0 import AsyncMemory
from psycopg_pool import AsyncConnectionPool

from app.core.config import (
    Environment,
    settings,
)
from app.core.langgraph.tools import tools
from app.core.logging import logger
from app.core.metrics import llm_inference_duration_seconds
from app.core.prompts import load_system_prompt
from app.business.chatbot.schemas import Message
from app.core.schemas import GraphState
from app.core.services.llm import llm_service
from app.utils.graph import (
    dump_messages,
    prepare_messages,
    process_llm_response,
)


class LangGraphAgent:
    """管理 LangGraph Agent/工作流以及与 LLM 的交互。

    此类处理 LangGraph 工作流的创建和管理，
    包括 LLM 交互、数据库连接和响应处理。
    """

    def __init__(self):
        """使用必要的组件初始化 LangGraph Agent。"""
        # 使用绑定了工具的 LLM 服务
        self.llm_service = llm_service
        self.llm_service.bind_tools(tools)
        self.tools_by_name = {tool.name: tool for tool in tools}
        self._connection_pool: Optional[AsyncConnectionPool] = None
        self._graph: Optional[CompiledStateGraph] = None
        self.memory: Optional[AsyncMemory] = None
        logger.info(
            "langgraph_agent_initialized",
            model=settings.DEFAULT_LLM_MODEL,
            environment=settings.ENVIRONMENT.value,
        )

    async def _long_term_memory(self) -> AsyncMemory:
        """初始化长期记忆。"""
        if self.memory is None:
            self.memory = await AsyncMemory.from_config(
                config_dict={
                    "vector_store": {
                        "provider": "pgvector",
                        "config": {
                            "collection_name": settings.LONG_TERM_MEMORY_COLLECTION_NAME,
                            "dbname": settings.POSTGRES_DB,
                            "user": settings.POSTGRES_USER,
                            "password": settings.POSTGRES_PASSWORD,
                            "host": settings.POSTGRES_HOST,
                            "port": settings.POSTGRES_PORT,
                        },
                    },
                    "llm": {
                        "provider": "openai",
                        "config": {"model": settings.LONG_TERM_MEMORY_MODEL},
                    },
                    "embedder": {"provider": "openai", "config": {"model": settings.LONG_TERM_MEMORY_EMBEDDER_MODEL}},
                    # "custom_fact_extraction_prompt": load_custom_fact_extraction_prompt(),
                }
            )
        return self.memory

    async def _get_connection_pool(self) -> AsyncConnectionPool:
        """使用环境特定的设置获取 PostgreSQL 连接池。

        返回:
            AsyncConnectionPool: PostgreSQL 数据库的连接池。
        """
        if self._connection_pool is None:
            try:
                # 根据环境配置连接池大小
                max_size = settings.POSTGRES_POOL_SIZE

                connection_url = (
                    "postgresql://"
                    f"{quote_plus(settings.POSTGRES_USER)}:{quote_plus(settings.POSTGRES_PASSWORD)}"
                    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
                )

                self._connection_pool = AsyncConnectionPool(
                    connection_url,
                    open=False,
                    max_size=max_size,
                    kwargs={
                        "autocommit": True,
                        "connect_timeout": 5,
                        "prepare_threshold": None,
                    },
                )
                await self._connection_pool.open()
                logger.info("connection_pool_created", max_size=max_size, environment=settings.ENVIRONMENT.value)
            except Exception as e:
                logger.error("connection_pool_creation_failed", error=str(e), environment=settings.ENVIRONMENT.value)
                # 在生产环境中，我们可能希望优雅降级
                if settings.ENVIRONMENT == Environment.PRODUCTION:
                    logger.warning("continuing_without_connection_pool", environment=settings.ENVIRONMENT.value)
                    return None
                raise e
        return self._connection_pool

    async def _get_relevant_memory(self, user_id: str, query: str) -> str:
        """获取用户和查询的相关记忆。

        参数:
            user_id (str): 用户 ID。
            query (str): 要搜索的查询。

        返回:
            str: 相关记忆。
        """
        try:
            memory = await self._long_term_memory()
            results = await memory.search(user_id=str(user_id), query=query)
            print(results)
            return "\n".join([f"* {result['memory']}" for result in results["results"]])
        except Exception as e:
            logger.error("failed_to_get_relevant_memory", error=str(e), user_id=user_id, query=query)
            return ""

    async def _update_long_term_memory(self, user_id: str, messages: list[dict], metadata: dict = None) -> None:
        """更新长期记忆。

        Args:
            user_id (str): 用户ID。
            messages (list[dict]): 用于更新长期记忆的消息。
            metadata (dict): 可选的元数据。
        """
        try:
            memory = await self._long_term_memory()
            await memory.add(messages, user_id=str(user_id), metadata=metadata)
            logger.info("long_term_memory_updated_successfully", user_id=user_id)
        except Exception as e:
            logger.exception(
                "failed_to_update_long_term_memory",
                user_id=user_id,
                error=str(e),
            )

    async def _chat(self, state: GraphState, config: RunnableConfig) -> Command:
        """处理聊天状态并生成响应。

        Args:
            state (GraphState): 当前对话的状态。

        Returns:
            Command: 包含更新后状态和下一个要执行的节点的命令对象。
        """
        # 获取当前LLM实例以用于指标记录
        current_llm = self.llm_service.get_llm()
        model_name = (
            current_llm.model_name
            if current_llm and hasattr(current_llm, "model_name")
            else settings.DEFAULT_LLM_MODEL
        )

        SYSTEM_PROMPT = load_system_prompt(long_term_memory=state.long_term_memory)

        # 使用系统提示词准备消息
        messages = prepare_messages(state.messages, current_llm, SYSTEM_PROMPT)

        try:
            # 使用LLM服务，支持自动重试和循环回退
            with llm_inference_duration_seconds.labels(model=model_name).time():
                response_message = await self.llm_service.call(dump_messages(messages))

            # 处理响应以处理结构化内容块
            response_message = process_llm_response(response_message)

            logger.info(
                "llm_response_generated",
                session_id=config["configurable"]["thread_id"],
                model=model_name,
                environment=settings.ENVIRONMENT.value,
            )

            # 根据是否有工具调用来决定下一个节点
            if response_message.tool_calls:
                goto = "tool_call"
            else:
                goto = END

            return Command(update={"messages": [response_message]}, goto=goto)
        except Exception as e:
            logger.error(
                "llm_call_failed_all_models",
                session_id=config["configurable"]["thread_id"],
                error=str(e),
                environment=settings.ENVIRONMENT.value,
            )
            raise Exception(f"failed to get llm response after trying all models: {str(e)}")

    # 定义工具节点
    async def _tool_call(self, state: GraphState) -> Command:
        """处理最后一条消息中的工具调用。

        Args:
            state: 当前代理状态，包含消息和工具调用。

        Returns:
            Command: 包含更新后的消息和路由回聊天节点的命令对象。
        """
        outputs = []
        for tool_call in state.messages[-1].tool_calls:
            tool_result = await self.tools_by_name[tool_call["name"]].ainvoke(tool_call["args"])
            outputs.append(
                ToolMessage(
                    content=tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return Command(update={"messages": outputs}, goto="chat")

    async def create_graph(self) -> Optional[CompiledStateGraph]:
        """创建并配置LangGraph工作流。

        Returns:
            Optional[CompiledStateGraph]: 配置好的LangGraph实例，如果初始化失败则返回None
        """
        if self._graph is None:
            try:
                graph_builder = StateGraph(GraphState)
                graph_builder.add_node("chat", self._chat, ends=["tool_call", END])
                graph_builder.add_node("tool_call", self._tool_call, ends=["chat"])
                graph_builder.set_entry_point("chat")
                graph_builder.set_finish_point("chat")

                # 获取连接池（如果数据库不可用，生产环境中可能为None）
                connection_pool = await self._get_connection_pool()
                if connection_pool:
                    checkpointer = AsyncPostgresSaver(connection_pool)
                    await checkpointer.setup()
                else:
                    # 在生产环境中，如果需要可以在没有检查点的情况下继续
                    checkpointer = None
                    if settings.ENVIRONMENT != Environment.PRODUCTION:
                        raise Exception("Connection pool initialization failed")

                self._graph = graph_builder.compile(
                    checkpointer=checkpointer, name=f"{settings.PROJECT_NAME} Agent ({settings.ENVIRONMENT.value})"
                )

                logger.info(
                    "graph_created",
                    graph_name=f"{settings.PROJECT_NAME} Agent",
                    environment=settings.ENVIRONMENT.value,
                    has_checkpointer=checkpointer is not None,
                )
            except Exception as e:
                logger.error("graph_creation_failed", error=str(e), environment=settings.ENVIRONMENT.value)
                # 在生产环境中，我们不希望应用崩溃
                if settings.ENVIRONMENT == Environment.PRODUCTION:
                    logger.warning("continuing_without_graph")
                    return None
                raise e

        return self._graph

    async def get_response(
        self,
        messages: list[Message],
        session_id: str,
        user_id: Optional[str] = None,
    ) -> list[dict]:
        """从LLM获取响应。

        Args:
            messages (list[Message]): 要发送给LLM的消息。
            session_id (str): 用于Langfuse跟踪的会话ID。
            user_id (Optional[str]): 用于Langfuse跟踪的用户ID。

        Returns:
            list[dict]: LLM的响应。
        """
        if self._graph is None:
            self._graph = await self.create_graph()
        config = {
            "configurable": {"thread_id": session_id},
            "callbacks": [CallbackHandler()],
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "environment": settings.ENVIRONMENT.value,
                "debug": settings.DEBUG,
            },
        }
        relevant_memory = (
            await self._get_relevant_memory(user_id, messages[-1].content)
        ) or "No relevant memory found."
        try:
            response = await self._graph.ainvoke(
                input={"messages": dump_messages(messages), "long_term_memory": relevant_memory},
                config=config,
            )
            # 在后台运行记忆更新，不阻塞响应
            asyncio.create_task(
                self._update_long_term_memory(
                    user_id, convert_to_openai_messages(response["messages"]), config["metadata"]
                )
            )
            return self.__process_messages(response["messages"])
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")

    async def get_stream_response(
        self, messages: list[Message], session_id: str, user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """从LLM获取流式响应。

        Args:
            messages (list[Message]): 要发送给LLM的消息。
            session_id (str): 对话的会话ID。
            user_id (Optional[str]): 对话的用户ID。

        Yields:
            str: LLM响应的令牌。
        """
        config = {
            "configurable": {"thread_id": session_id},
            "callbacks": [
                CallbackHandler(
                    environment=settings.ENVIRONMENT.value, debug=False, user_id=user_id, session_id=session_id
                )
            ],
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "environment": settings.ENVIRONMENT.value,
                "debug": settings.DEBUG,
            },
        }
        if self._graph is None:
            self._graph = await self.create_graph()

        relevant_memory = (
            await self._get_relevant_memory(user_id, messages[-1].content)
        ) or "No relevant memory found."

        try:
            async for token, _ in self._graph.astream(
                {"messages": dump_messages(messages), "long_term_memory": relevant_memory},
                config,
                stream_mode="messages",
            ):
                try:
                    yield token.content
                except Exception as token_error:
                    logger.error("Error processing token", error=str(token_error), session_id=session_id)
                    # 即使当前令牌失败也继续处理下一个令牌
                    continue

            # 流式传输完成后，获取最终状态并在后台更新记忆
            state: StateSnapshot = await sync_to_async(self._graph.get_state)(config=config)
            if state.values and "messages" in state.values:
                asyncio.create_task(
                    self._update_long_term_memory(
                        user_id, convert_to_openai_messages(state.values["messages"]), config["metadata"]
                    )
                )
        except Exception as stream_error:
            logger.error("Error in stream processing", error=str(stream_error), session_id=session_id)
            raise stream_error

    async def get_chat_history(self, session_id: str) -> list[Message]:
        """获取给定线程ID的聊天历史。

        Args:
            session_id (str): 对话的会话ID。

        Returns:
            list[Message]: 聊天历史。
        """
        if self._graph is None:
            self._graph = await self.create_graph()

        state: StateSnapshot = await sync_to_async(self._graph.get_state)(
            config={"configurable": {"thread_id": session_id}}
        )
        return self.__process_messages(state.values["messages"]) if state.values else []

    def __process_messages(self, messages: list[BaseMessage]) -> list[Message]:
        openai_style_messages = convert_to_openai_messages(messages)
        # 仅保留助手和用户消息
        return [
            Message(role=message["role"], content=str(message["content"]))
            for message in openai_style_messages
            if message["role"] in ["assistant", "user"] and message["content"]
        ]

    async def clear_chat_history(self, session_id: str) -> None:
        """清除给定线程ID的所有聊天历史。

        Args:
            session_id: 要清除历史的会话ID。

        Raises:
            Exception: 如果清除聊天历史时出错。
        """
        try:
            # 确保连接池在当前事件循环中已初始化
            conn_pool = await self._get_connection_pool()

            # 为此特定操作使用新连接
            async with conn_pool.connection() as conn:
                for table in settings.CHECKPOINT_TABLES:
                    try:
                        await conn.execute(f"DELETE FROM {table} WHERE thread_id = %s", (session_id,))
                        logger.info(f"Cleared {table} for session {session_id}")
                    except Exception as e:
                        logger.error(f"Error clearing {table}", error=str(e))
                        raise

        except Exception as e:
            logger.error("Failed to clear chat history", error=str(e))
            raise
