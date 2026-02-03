"""应用程序的Prometheus指标配置。

该模块为监控应用程序设置和配置Prometheus指标。
"""

from prometheus_client import Counter, Histogram, Gauge
from starlette_prometheus import metrics, PrometheusMiddleware

# 请求指标
http_requests_total = Counter("http_requests_total", "Total number of HTTP requests", ["method", "endpoint", "status"])

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request duration in seconds", ["method", "endpoint"]
)

# 数据库指标
db_connections = Gauge("db_connections", "Number of active database connections")

# 自定义业务指标
orders_processed = Counter("orders_processed_total", "Total number of orders processed")

llm_inference_duration_seconds = Histogram(
    "llm_inference_duration_seconds",
    "Time spent processing LLM inference",
    ["model"],
    buckets=[0.1, 0.3, 0.5, 1.0, 2.0, 5.0],
)


llm_stream_duration_seconds = Histogram(
    "llm_stream_duration_seconds",
    "Time spent processing LLM stream inference",
    ["model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)


def setup_metrics(app):
    """设置Prometheus指标中间件和端点。

    Args:
        app: FastAPI应用程序实例
    """
    # 添加Prometheus中间件
    app.add_middleware(PrometheusMiddleware)

    # 添加指标端点
    app.add_route("/metrics", metrics)
