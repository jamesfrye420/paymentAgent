"""Circuit breaker implementation for fault tolerance."""

import time
from datetime import datetime, timedelta
from typing import Callable, Any

from ..core.enums import CircuitBreakerState
from ..core.exceptions import CircuitBreakerError
from ..core.models import CircuitBreakerConfig


class CircuitBreaker:
    """
    Circuit breaker implementation following the circuit breaker pattern.

    Prevents cascading failures by monitoring failure rates and temporarily
    stopping calls to failing services.
    """

    def __init__(self, config: CircuitBreakerConfig = None):
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self.half_open_calls = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function call through circuit breaker.

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: When circuit breaker is open
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")

        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                raise CircuitBreakerError(
                    "Circuit breaker HALF_OPEN call limit exceeded"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if not self.last_failure_time:
            return True

        timeout_elapsed = datetime.now() - self.last_failure_time
        return timeout_elapsed >= timedelta(seconds=self.config.timeout_seconds)

    def _on_success(self):
        """Handle successful call."""
        self.success_count += 1

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.config.half_open_max_calls:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = max(0, self.failure_count - 1)

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Any failure in HALF_OPEN state moves back to OPEN
            self.state = CircuitBreakerState.OPEN
        elif self.state == CircuitBreakerState.CLOSED:
            # Check if failure threshold exceeded
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN

    def force_open(self):
        """Force circuit breaker to OPEN state."""
        self.state = CircuitBreakerState.OPEN
        self.last_failure_time = datetime.now()

    def force_close(self):
        """Force circuit breaker to CLOSED state and reset counters."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time = None

    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self.state

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
            "half_open_calls": self.half_open_calls,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "half_open_max_calls": self.config.half_open_max_calls,
            },
        }
