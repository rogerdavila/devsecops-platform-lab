from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

REGISTRY = CollectorRegistry()

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
    registry=REGISTRY,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    registry=REGISTRY,
)

http_requests_errors_total = Counter(
    "http_requests_errors_total",
    "Total HTTP error requests (status >= 500)",
    ["method", "path", "status"],
    registry=REGISTRY,
)

process_uptime_seconds = Gauge(
    "process_uptime_seconds",
    "Seconds since process start",
    registry=REGISTRY,
)
