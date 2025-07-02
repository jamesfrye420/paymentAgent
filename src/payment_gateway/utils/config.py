"""Configuration management for the payment gateway system."""

import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Config:
    """Configuration class for payment gateway system."""
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    # Payment defaults
    default_currency: str = "USD"
    max_retry_attempts: int = 3
    retry_backoff_multiplier: float = 2.0
    initial_retry_delay: float = 1.0
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: int = 30
    circuit_breaker_half_open_max_calls: int = 3
    
    # Monitoring settings
    monitoring_enabled: bool = True
    metrics_retention_hours: int = 24
    health_check_interval: int = 10
    
    # Provider settings
    provider_rate_limit_threshold: int = 100
    provider_rate_limit_window: int = 60
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        return cls(
            environment=os.getenv('PAYMENT_GATEWAY_ENV', 'development'),
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            default_currency=os.getenv('DEFAULT_CURRENCY', 'USD'),
            max_retry_attempts=int(os.getenv('MAX_RETRY_ATTEMPTS', '3')),
            retry_backoff_multiplier=float(os.getenv('RETRY_BACKOFF_MULTIPLIER', '2.0')),
            initial_retry_delay=float(os.getenv('INITIAL_RETRY_DELAY', '1.0')),
            circuit_breaker_failure_threshold=int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '5')),
            circuit_breaker_timeout=int(os.getenv('CIRCUIT_BREAKER_TIMEOUT', '30')),
            circuit_breaker_half_open_max_calls=int(os.getenv('CIRCUIT_BREAKER_HALF_OPEN_CALLS', '3')),
            monitoring_enabled=os.getenv('MONITORING_ENABLED', 'true').lower() == 'true',
            metrics_retention_hours=int(os.getenv('METRICS_RETENTION_HOURS', '24')),
            health_check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL', '10')),
            provider_rate_limit_threshold=int(os.getenv('PROVIDER_RATE_LIMIT_THRESHOLD', '100')),
            provider_rate_limit_window=int(os.getenv('PROVIDER_RATE_LIMIT_WINDOW', '60'))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'environment': self.environment,
            'debug': self.debug,
            'default_currency': self.default_currency,
            'max_retry_attempts': self.max_retry_attempts,
            'retry_backoff_multiplier': self.retry_backoff_multiplier,
            'initial_retry_delay': self.initial_retry_delay,
            'circuit_breaker_failure_threshold': self.circuit_breaker_failure_threshold,
            'circuit_breaker_timeout': self.circuit_breaker_timeout,
            'circuit_breaker_half_open_max_calls': self.circuit_breaker_half_open_max_calls,
            'monitoring_enabled': self.monitoring_enabled,
            'metrics_retention_hours': self.metrics_retention_hours,
            'health_check_interval': self.health_check_interval,
            'provider_rate_limit_threshold': self.provider_rate_limit_threshold,
            'provider_rate_limit_window': self.provider_rate_limit_window
        }
    
    def update(self, **kwargs):
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")


# Global configuration instance
config = Config.from_env()