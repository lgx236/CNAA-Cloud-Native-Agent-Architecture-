"""CNAA metrics export for Prometheus monitoring."""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Base metric definition."""
    name: str
    description: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram


class MetricsCollector:
    """Collect and export metrics from CNAA components."""
    
    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._start_time = time.time()
        self._request_counts = defaultdict(int)
        self._request_latencies = defaultdict(list)
        
        # Pre-define standard metrics
        self._standard_metric_names = [
            "cnaa_memory_count",
            "cnaa_state_count",
            "cnaa_request_total",
            "cnaa_request_latency_seconds",
            "cnaa_error_total",
            "cnaa_uptime_seconds"
        ]
    
    def record_memory_count(self, count: int, agent_id: str = "unknown"):
        """Record memory count metric."""
        metric = Metric(
            name="cnaa_memory_count",
            description="Total number of memories stored",
            value=float(count),
            labels={"agent_id": agent_id}
        )
        self._store_metric(metric)
    
    def record_state_count(self, count: int, category: str = "general"):
        """Record state count metric."""
        metric = Metric(
            name="cnaa_state_count",
            description="Total number of state entries",
            value=float(count),
            labels={"category": category}
        )
        self._store_metric(metric)
    
    def record_request_start(self, operation: str, method: str = "GET"):
        """Record request start for latency tracking."""
        self._request_counts[operation] += 1
        self._request_latencies[operation].append(time.time())
    
    def record_request_complete(self, operation: str, success: bool):
        """Record request completion and latency."""
        latencies = self._request_latencies[operation]
        if latencies:
            elapsed = time.time() - latencies.pop(0)
            
            metric = Metric(
                name="cnaa_request_latency_seconds",
                description="Request latency in seconds",
                value=elapsed,
                labels={
                    "operation": operation,
                    "success": "true" if success else "false"
                },
                metric_type="histogram"
            )
            self._store_metric(metric)
    
    def record_error(self, error_type: str, operation: str = "unknown"):
        """Record an error event."""
        metric = Metric(
            name="cnaa_error_total",
            description="Total number of errors",
            value=1.0,
            labels={
                "error_type": error_type,
                "operation": operation
            }
        )
        self._increment_metric("cnaa_error_total", {"error_type": error_type}, 1)
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds."""
        return time.time() - self._start_time
    
    def _store_metric(self, metric: Metric):
        """Store a metric in the collector."""
        key = f"{metric.name}:{str(metric.labels)}"
        self._metrics[key] = metric
    
    def _increment_metric(self, name: str, labels: Dict[str, str], increment: float = 1.0):
        """Increment existing metric or create new one."""
        labels_str = str(labels)
        current = self._metrics.get(f"{name}:{labels_str}")
        
        if current:
            current.value += increment
        else:
            metric = Metric(
                name=name,
                description="Counter metric",
                value=increment,
                labels=labels
            )
            self._metrics[f"{name}:{labels_str}"] = metric
    
    def collect_all(self) -> List[Metric]:
        """Collect all current metrics."""
        return list(self._metrics.values())
    
    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        
        # Sort metrics by name
        sorted_metrics = sorted(self._metrics.values(), key=lambda m: m.name)
        
        for metric in sorted_metrics:
            # Add type hint comment
            if not any(lines.endswith(f"# TYPE {metric.name} {metric.metric_type}") 
                      for lines in lines.split('\n')):
                lines.append(f"# TYPE {metric.name} {metric.metric_type}")
            
            # Add help text
            lines.append(f"# HELP {metric.name} {metric.description}")
            
            # Format metric line
            if metric.labels:
                label_str = ",".join(
                    f'{k}="{v}"' for k, v in sorted(metric.labels.items())
                )
                metric_line = f"{metric.name}{{{label_str}}} {metric.value:.2f}"
            else:
                metric_line = f"{metric.name} {metric.value:.2f}"
            
            lines.append(metric_line)
        
        # Add special runtime metrics
        lines.extend([
            "# TYPE cnaa_runtime_info gauge",
            "# HELP cnaa_runtime_info CNAA runtime information",
            f"cnaa_runtime_info{{version=\"1.0.0\"}} 1"
        ])
        
        return "\n".join(lines)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary as dictionary."""
        return {
            "total_metrics": len(self._metrics),
            "uptime_seconds": self.get_uptime(),
            "memory_counts": sum(
                m.value for m in self._metrics.values() 
                if m.name == "cnaa_memory_count"
            ),
            "state_counts": sum(
                m.value for m in self._metrics.values()
                if m.name == "cnaa_state_count"
            ),
            "error_count": sum(
                m.value for m in self._metrics.values()
                if m.name == "cnaa_error_total"
            ),
            "latest_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }


# Global instance for module-level access
_default_collector: Optional[MetricsCollector] = None


def get_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _default_collector
    if _default_collector is None:
        _default_collector = MetricsCollector()
    return _default_collector


def collect_and_export() -> str:
    """Quick function to collect and export all metrics."""
    return get_collector().to_prometheus_format()


if __name__ == "__main__":
    print(collect_and_export())
