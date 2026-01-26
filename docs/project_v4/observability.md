# LDUP v4 Observability Strategy

**Goal:** Full visibility into system behavior through **structured logging** (loguru) and metrics.

---

## Why Observability Matters

### Without Observability (v3 Problem)
- "Why did document 123 fail?" → No logs, can't debug
- "How many LLM calls per document?" → No metrics, can't optimize
- "Which rules were applied?" → No trace, can't verify
- "Is self-improvement working?" → No tracking, can't measure

### With Observability (v4 Solution)
```python
logger.bind(document_id=123, source="consultantplus").info("Processing")
# Output: 2026-01-18 12:00:00 | INFO | parse:125 - Processing document_id=123 source=consultantplus
```

---

## loguru Configuration

### Basic Setup

```python
from loguru import logger
import sys

# Remove default handler
logger.remove()

# 1. Console (development) - Colorized, human-readable
logger.add(
    sys.stdout,
    level="DEBUG",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
    backtrace=True,  # Full traceback on error
    diagnose=True    # Variable values on error
)

# 2. File (production) - JSON lines, machine-readable
logger.add(
    "logs/app.log",
    level="INFO",
    format="{message}",  # JSON serialization via serialize=True
    rotation="1 day",     # New file daily
    retention="7 days",   # Keep 7 days
    compression="zip",    # Compress old files
    serialize=True,       # JSON lines format
    enqueue=True,         # Thread-safe
)

# 3. Error-only file - For alerting
logger.add(
    "logs/errors.log",
    level="ERROR",
    format="{message}",
    rotation="1 week",
    retention="30 days",
    serialize=True
)

# 4. LLM trace file - For debugging prompts
logger.add(
    "logs/llm_trace.log",
    level="DEBUG",
    filter=lambda record: "llm" in record["extra"].get("tags", []),
    format="{message}",
    rotation="1 day",
    retention="3 days",
    serialize=True
)
```

### Output Format Examples

#### Console (Development)
```
12:00:00 | INFO     | parse:process_document:125 - Processing document_id=123 source=consultantplus
12:00:01 | DEBUG    | parse:_call_llm:67 - LLM call document_id=123 prompt_length=1234
12:00:02 | INFO     | parse:process_document:145 - Document parsed document_id=123 chapters=10 articles=50
12:00:03 | WARNING  | validate:check_temporal:89 - Invalid interval document_id=123 article_id=5 valid_from=2026-01-01 valid_to=2025-01-01
12:00:04 | ERROR    | validate:check_structure:45 - Orphan article document_id=123 article_id=7
```

#### File (Production - JSON Lines)
```jsonl
{"time": "2026-01-18T12:00:00.123Z", "level": "INFO", "name": "parse", "function": "process_document", "line": 125, "message": "Processing document", "document_id": 123, "source": "consultantplus"}
{"time": "2026-01-18T12:00:01.234Z", "level": "DEBUG", "name": "parse", "function": "_call_llm", "line": 67, "message": "LLM call", "document_id": 123, "prompt_length": 1234, "tags": ["llm"]}
{"time": "2026-01-18T12:00:02.345Z", "level": "INFO", "name": "parse", "function": "process_document", "line": 145, "message": "Document parsed", "document_id": 123, "chapters": 10, "articles": 50}
```

---

## Logging Levels

### Level Definitions

| Level | Use Case | Example | Output Target |
|-------|----------|---------|---------------|
| **TRACE** | Extreme detail (rare) | Variable values, internal states | Console only |
| **DEBUG** | LLM prompts/responses | Full prompt for debugging | Console + LLM trace |
| **INFO** | Normal operations | "Processing document", "Export complete" | Console + File |
| **WARNING** | Unexpected but OK | Fallback path used, missing metadata | Console + File |
| **ERROR** | Failure but continue | Parse failure, validation error | Console + Error file |
| **CRITICAL** | System failure | LLM API timeout, abort required | Console + Error file + Alert |

### Level Usage Examples

```python
from loguru import logger

# DEBUG: LLM calls (for debugging)
logger.bind(
    document_id=doc.id,
    prompt_length=len(prompt),
    model="gpt-4"
).debug("LLM call", extra={"tags": ["llm"], "prompt": prompt})

# INFO: Processing steps
logger.bind(
    document_id=doc.id,
    source=doc.source_type,
    text_length=len(doc.text)
).info("Starting ingestion")

# WARNING: Fallback paths
logger.bind(
    document_id=doc.id,
    article_id=article.id,
    reason="missing_parent"
).warning("Article without parent, using default")

# ERROR: Parse failures
try:
    result = parse_complex_structure(doc)
except ParseError as e:
    logger.bind(
        document_id=doc.id,
        error_type="parse_failure",
        error_details=str(e)
    ).error("Failed to parse structure")

# CRITICAL: System failures
try:
    result = llm_client.call(prompt)
except LLMTimeoutError as e:
    logger.bind(
        error="llm_timeout",
        timeout_seconds=30
    ).critical("LLM API timeout, aborting")
    raise SystemAbort("LLM service unavailable")
```

---

## Structured Logging

### Binding Context

```python
from loguru import logger

# Bind context once
doc_logger = logger.bind(
    document_id=doc.id,
    source_type=doc.source_type,
    ingestion_timestamp=datetime.now(timezone.utc).isoformat()
)

# All subsequent calls include context
doc_logger.info("Ingestion started")
doc_logger.debug("Text extracted", text_length=len(doc.text))
doc_logger.info("Source detected", source="consultantplus")
```

### Extra Fields

```python
logger.info(
    "Processing complete",
    extra={
        "document_id": doc.id,
        "processing_time_seconds": 3.5,
        "llm_calls": 25,
        "cache_hits": 10,
        "chapters": 10,
        "articles": 50
    }
)
```

### Serialization

```python
# Custom object serialization
from loguru import logger

class LegalDocument:
    def __init__(self, id, title, chapters):
        self.id = id
        self.title = title
        self.chapters = chapters

# Register serializer
logger.patch(lambda record: record["extra"].update(
    document={
        "id": doc.id,
        "title": doc.title,
        "chapter_count": len(doc.chapters)
    }
))

logger.info("Document processed")
# Output: {"extra": {"document": {"id": 123, "title": "44-FZ", "chapter_count": 10}}}
```

---

## Performance Logging

### Timing Operations

```python
import time
from loguru import logger
from functools import wraps

def log_execution_time(logger, operation):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.bind(
                    operation=operation,
                    duration_seconds=duration
                ).info("Operation completed")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.bind(
                    operation=operation,
                    duration_seconds=duration,
                    error=str(e)
                ).error("Operation failed")
                raise
        return wrapper
    return decorator

# Usage
@log_execution_time(logger, "parse_document")
def parse_document(doc):
    # ... parsing logic ...
    return result
```

### LLM Call Tracking

```python
from loguru import logger

llm_call_counter = 0

def call_llm_with_logging(prompt, model="gpt-4"):
    global llm_call_counter
    llm_call_counter += 1

    start = time.time()
    response = llm_client.call(prompt, model=model)
    duration = time.time() - start

    logger.bind(
        llm_call_number=llm_call_counter,
        model=model,
        prompt_tokens=len(prompt.split()),
        duration_seconds=duration,
        estimated_cost=estimate_cost(prompt, response, model)
    ).debug("LLM call", extra={"tags": ["llm"], "prompt": prompt[:100]})

    return response
```

---

## Metrics Collection

### What to Measure

| Metric | Type | Description |
|--------|------|-------------|
| **documents_processed** | Counter | Total documents processed |
| **llm_calls_total** | Counter | Total LLM calls |
| **llm_calls_per_document** | Histogram | LLM calls per document |
| **cache_hit_rate** | Gauge | % cache hits |
| **parse_time_seconds** | Histogram | Time to parse document |
| **validation_errors** | Counter | Validation errors by type |
| **accuracy_by_source** | Gauge | Accuracy per source type |
| **self_improvement_iterations** | Counter | Self-improvement loop iterations |
| **rule_activations** | Counter | Rules promoted to active |

### Metrics Implementation

```python
from collections import defaultdict
from loguru import logger

class MetricsCollector:
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)

    def increment(self, metric, value=1, tags=None):
        self.counters[metric] += value
        logger.bind(metric=metric, value=value, tags=tags or {}).debug("Counter increment")

    def set_gauge(self, metric, value, tags=None):
        self.gauges[metric] = value
        logger.bind(metric=metric, value=value, tags=tags or {}).debug("Gauge set")

    def record_histogram(self, metric, value, tags=None):
        self.histograms[metric].append(value)
        logger.bind(metric=metric, value=value, tags=tags or {}).debug("Histogram record")

    def get_summary(self):
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                k: {
                    "count": len(v),
                    "min": min(v),
                    "max": max(v),
                    "avg": sum(v) / len(v)
                }
                for k, v in self.histograms.items()
            }
        }

# Global instance
metrics = MetricsCollector()

# Usage
metrics.increment("documents_processed", tags={"source": "consultantplus"})
metrics.record_histogram("parse_time_seconds", 3.5, tags={"document_id": 123})
metrics.set_gauge("cache_hit_rate", 0.85, tags={"cache_type": "hco"})
```

### Periodic Metrics Logging

```python
import time
from threading import Thread

class MetricsReporter(Thread):
    def __init__(self, collector, interval_seconds=60):
        super().__init__()
        self.collector = collector
        self.interval = interval_seconds
        self.daemon = True

    def run(self):
        while True:
            time.sleep(self.interval)
            summary = self.collector.get_summary()
            logger.bind(
                metrics_summary=summary,
                interval_seconds=self.interval
            ).info("Metrics report")

# Start reporter
reporter = MetricsReporter(metrics, interval_seconds=60)
reporter.start()
```

---

## Alerting

### Error Alerts

```python
from loguru import logger

class AlertHandler:
    def __init__(self, logger, error_threshold=10):
        self.logger = logger
        self.error_threshold = error_threshold
        self.error_count = 0
        self.reset_time = time.time() + 60  # Reset every minute

    def check(self, record):
        if record["level"].name == "ERROR":
            self.error_count += 1

            if self.error_count >= self.error_threshold:
                # Send alert
                self.logger.critical(
                    f"Error threshold exceeded: {self.error_count} errors in window"
                )
                # Send to external service
                send_alert_to_slack(
                    f"LDUP: {self.error_count} errors in last minute"
                )
                send_alert_to_prometheus(
                    metric="ldup_errors_total",
                    value=self.error_count
                )

        if time.time() > self.reset_time:
            self.error_count = 0
            self.reset_time = time.time() + 60

# Add to logger
alert_handler = AlertHandler(logger)
logger.add(lambda r: alert_handler.check(r))
```

### Custom Alerts

```python
def send_alert_to_slack(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if webhook_url:
        requests.post(webhook_url, json={"text": message})

def send_alert_to_prometheus(metric, value):
    # Push to Prometheus Pushgateway
    pass
```

---

## Integration with External Tools

### MLflow Integration

```python
import mlflow

with mlflow.start_run():
    # Log parameters
    mlflow.log_param("model", "gpt-4")
    mlflow.log_param("gepa_iterations", 10)

    # Log metrics
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("llm_calls_total", 5000)

    # Log artifacts
    mlflow.log_artifact("cache/graph.pkl")
```

### Prometheus Integration

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
documents_processed = Counter('ldup_documents_processed_total', 'Total documents processed')
parse_time = Histogram('ldup_parse_duration_seconds', 'Time to parse document')
cache_hit_rate = Gauge('ldup_cache_hit_rate', 'Cache hit rate')

# Usage
documents_processed.labels(source="consultantplus").inc()
parse_time.observe(3.5)
cache_hit_rate.set(0.85)
```

---

## Log Analysis

### Querying Logs (jq)

```bash
# Count errors per document
cat logs/app.log | jq 'select(.level == "ERROR") | group_by(.document_id) | map({document_id: .[0].document_id, count: length})'

# Average parse time
cat logs/app.log | jq 'select(.message == "Operation completed") | .duration_seconds' | awk '{sum+=$1; count++} END {print sum/count}'

# LLM calls per document
cat logs/app.log | jq '[select(.tags | contains(["llm"])) | group_by(.document_id) | map({document_id: .[0].document_id, count: length})]'
```

### LogQL (Grafana Loki)

```
# Errors in last hour
{level="ERROR"} | json | line_format "{{.document_id}}: {{.error_type}}"

# Parse time percentiles
{operation="parse_document"} | json | quantile_over_time(0.95, duration_seconds[1h])

# Cache hit rate over time
(sum(rate({cache_hit="true"}[5m])) / sum(rate({cache_hit="true"} or {cache_hit="false"}[5m])))
```

---

## Best Practices

### DO ✅
- Use structured logging with `bind()` for context
- Log at appropriate levels (DEBUG for LLM, INFO for operations)
- Include document_id in all logs for traceability
- Use JSON lines for file logs (machine-readable)
- Rotate logs daily, keep 7 days
- Use metrics for trending (not logs)
- Alert on critical errors and threshold breaches

### DON'T ❌
- Don't log full LLM prompts in INFO (use DEBUG)
- Don't log sensitive data (PII, API keys)
- Don't ignore WARNING messages (fix root cause)
- Don't keep logs indefinitely (cost, privacy)
- Don't log to stdout in production (use files)

---

## References

- loguru docs: https://loguru.readthedocs.io
- Prometheus client: https://prometheus_client.readthedocs.io
- MLflow: https://mlflow.org
