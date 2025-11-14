"""Metrics collection for monitoring and observability."""

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, Optional


@dataclass
class SensorMetrics:
    """Metrics for a single sensor."""
    
    sensor_id: str
    messages_sent: int = 0
    errors: int = 0
    last_update: Optional[float] = None
    avg_latency_ms: float = 0.0
    latency_samples: list = field(default_factory=list)
    
    def record_message(self, latency_ms: Optional[float] = None) -> None:
        """Record a successful message send."""
        self.messages_sent += 1
        self.last_update = time.time()
        if latency_ms is not None:
            self.latency_samples.append(latency_ms)
            # Keep only last 100 samples for rolling average
            if len(self.latency_samples) > 100:
                self.latency_samples.pop(0)
            if self.latency_samples:
                self.avg_latency_ms = sum(self.latency_samples) / len(self.latency_samples)
    
    def record_error(self) -> None:
        """Record an error."""
        self.errors += 1
        self.last_update = time.time()


class MetricsCollector:
    """Thread-safe metrics collector."""
    
    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._sensors: Dict[str, SensorMetrics] = {}
        self._lock = Lock()
        self._start_time = time.time()
        self._total_entities = 0
        self._active_entities = 0
    
    def get_or_create_sensor(self, sensor_id: str) -> SensorMetrics:
        """Get or create metrics for a sensor."""
        with self._lock:
            if sensor_id not in self._sensors:
                self._sensors[sensor_id] = SensorMetrics(sensor_id=sensor_id)
            return self._sensors[sensor_id]
    
    def record_message(self, sensor_id: str, latency_ms: Optional[float] = None) -> None:
        """Record a message sent by a sensor."""
        sensor = self.get_or_create_sensor(sensor_id)
        sensor.record_message(latency_ms)
    
    def record_error(self, sensor_id: str) -> None:
        """Record an error for a sensor."""
        sensor = self.get_or_create_sensor(sensor_id)
        sensor.record_error()
    
    def update_entity_counts(self, total: int, active: int) -> None:
        """Update entity counts."""
        with self._lock:
            self._total_entities = total
            self._active_entities = active
    
    def get_summary(self) -> Dict:
        """Get a summary of all metrics."""
        with self._lock:
            total_messages = sum(s.messages_sent for s in self._sensors.values())
            total_errors = sum(s.errors for s in self._sensors.values())
            uptime_seconds = time.time() - self._start_time
            
            return {
                "uptime_seconds": uptime_seconds,
                "total_messages": total_messages,
                "total_errors": total_errors,
                "error_rate": total_errors / max(total_messages, 1),
                "total_entities": self._total_entities,
                "active_entities": self._active_entities,
                "sensors": {
                    sensor_id: {
                        "messages_sent": s.messages_sent,
                        "errors": s.errors,
                        "avg_latency_ms": s.avg_latency_ms,
                        "last_update": s.last_update,
                    }
                    for sensor_id, s in self._sensors.items()
                },
            }
    
    def get_sensor_metrics(self, sensor_id: str) -> Optional[SensorMetrics]:
        """Get metrics for a specific sensor."""
        with self._lock:
            return self._sensors.get(sensor_id)
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._sensors.clear()
            self._start_time = time.time()
            self._total_entities = 0
            self._active_entities = 0

