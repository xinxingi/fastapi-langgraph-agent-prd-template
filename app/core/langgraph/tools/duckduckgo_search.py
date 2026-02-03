"""LangGraph 的 DuckDuckGo 搜索工具。

此模块提供了一个 DuckDuckGo 搜索工具，可与 LangGraph 一起使用
来执行网络搜索。它最多返回 10 个搜索结果，并能优雅地处理错误。
"""

from langchain_community.tools import DuckDuckGoSearchResults

duckduckgo_search_tool = DuckDuckGoSearchResults(num_results=10, handle_tool_error=True)
