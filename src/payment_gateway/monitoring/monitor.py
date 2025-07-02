"""Payment monitoring and event system."""

import time
import threading
from datetime import datetime
from typing import List, Callable, Dict, Any
from collections import defaultdict, deque

from ..core.models import PaymentEvent


class PaymentMonitor:
    """
    Payment monitoring system with event emission and metrics collection.

    Provides real-time monitoring capabilities for payment transactions,
    provider health, and system metrics.
    """

    def __init__(self, max_metrics_history: int = 1000):
        """
        Initialize payment monitor.

        Args:
            max_metrics_history: Maximum number of metrics to keep in memory
        """
        self.observers: List[Callable[[PaymentEvent], None]] = []
        self.metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_metrics_history)
        )
        self.running = False
        self.monitor_thread = None
        self._lock = threading.Lock()

    def add_observer(self, observer: Callable[[PaymentEvent], None]):
        """
        Add an observer to receive payment events.

        Args:
            observer: Callable that receives PaymentEvent
        """
        with self._lock:
            self.observers.append(observer)

    def remove_observer(self, observer: Callable[[PaymentEvent], None]):
        """
        Remove an observer from receiving payment events.

        Args:
            observer: Observer to remove
        """
        with self._lock:
            if observer in self.observers:
                self.observers.remove(observer)

    def emit_event(self, event: PaymentEvent):
        """
        Emit a payment event to all observers.

        Args:
            event: PaymentEvent to emit
        """
        with self._lock:
            observers_copy = self.observers.copy()

        for observer in observers_copy:
            try:
                observer(event)
            except Exception as e:
                print(f"Observer error: {e}")

    def record_metric(self, metric_name: str, value: Any, timestamp: datetime = None):
        """
        Record a metric value.

        Args:
            metric_name: Name of the metric
            value: Metric value
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        metric_entry = {"value": value, "timestamp": timestamp}

        with self._lock:
            self.metrics[metric_name].append(metric_entry)

    def get_metrics(self, metric_name: str = None) -> Dict[str, Any]:
        """
        Get metrics data.

        Args:
            metric_name: Specific metric name (optional)

        Returns:
            Dictionary of metrics data
        """
        with self._lock:
            if metric_name:
                return {metric_name: list(self.metrics.get(metric_name, []))}
            else:
                return {name: list(values) for name, values in self.metrics.items()}

    def get_metric_summary(
        self, metric_name: str, window_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Get summary statistics for a metric within a time window.

        Args:
            metric_name: Name of the metric
            window_minutes: Time window in minutes

        Returns:
            Summary statistics
        """
        with self._lock:
            if metric_name not in self.metrics:
                return {}

            cutoff_time = datetime.now()
            cutoff_time = cutoff_time.replace(
                minute=cutoff_time.minute - window_minutes, second=0, microsecond=0
            )

            recent_values = [
                entry["value"]
                for entry in self.metrics[metric_name]
                if entry["timestamp"] >= cutoff_time
            ]

            if not recent_values:
                return {"count": 0}

            # Calculate basic statistics
            return {
                "count": len(recent_values),
                "min": min(recent_values) if recent_values else 0,
                "max": max(recent_values) if recent_values else 0,
                "avg": sum(recent_values) / len(recent_values) if recent_values else 0,
                "total": (
                    sum(recent_values)
                    if isinstance(recent_values[0], (int, float))
                    else len(recent_values)
                ),
            }

    def clear_metrics(self, metric_name: str = None):
        """
        Clear metrics data.

        Args:
            metric_name: Specific metric to clear (clears all if None)
        """
        with self._lock:
            if metric_name:
                if metric_name in self.metrics:
                    self.metrics[metric_name].clear()
            else:
                self.metrics.clear()

    def start_monitoring(self):
        """Start the monitoring background thread."""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True
            )
            self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop the monitoring background thread."""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.running:
            try:
                # Record system metrics
                self.record_metric("monitor_heartbeat", 1)

                # Sleep for a short interval
                time.sleep(1)
            except Exception as e:
                print(f"Monitor loop error: {e}")

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide monitoring statistics."""
        with self._lock:
            total_events = sum(len(values) for values in self.metrics.values())
            active_metrics = len(self.metrics)

            return {
                "total_events_recorded": total_events,
                "active_metrics": active_metrics,
                "active_observers": len(self.observers),
                "monitoring_active": self.running,
                "uptime_seconds": self._get_uptime(),
            }

    def _get_uptime(self) -> float:
        """Get monitoring uptime in seconds."""
        # Simple implementation - in production might track start time
        heartbeat_metrics = self.metrics.get("monitor_heartbeat", [])
        if heartbeat_metrics:
            first_heartbeat = heartbeat_metrics[0]["timestamp"]
            return (datetime.now() - first_heartbeat).total_seconds()
        return 0.0

    def __del__(self):
        """Cleanup when monitor is destroyed."""
        self.stop_monitoring()
