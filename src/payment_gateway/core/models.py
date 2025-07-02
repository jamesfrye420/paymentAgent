"""Enhanced data models for the payment gateway system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from .enums import (
    PaymentStatus,
    CardNetwork,
    PaymentMethod,
    Currency,
    TransactionType,
    RiskLevel,
    Region,
)


@dataclass
class PaymentInstrument:
    """Represents a payment instrument (card, wallet, etc.)."""

    method: PaymentMethod
    network: Optional[CardNetwork] = None
    last_four: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    country_code: Optional[str] = None
    issuer: Optional[str] = None
    brand: Optional[str] = None  # e.g., "visa_debit", "mastercard_credit"
    wallet_type: Optional[str] = None  # e.g., "apple_pay", "google_pay"

    def to_dict(self) -> Dict[str, Any]:
        """Convert payment instrument to dictionary."""
        return {
            "method": self.method.value,
            "network": self.network.value if self.network else None,
            "last_four": self.last_four,
            "expiry_month": self.expiry_month,
            "expiry_year": self.expiry_year,
            "country_code": self.country_code,
            "issuer": self.issuer,
            "brand": self.brand,
            "wallet_type": self.wallet_type,
        }


@dataclass
class CustomerInfo:
    """Customer information for risk assessment and routing."""

    customer_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    region: Optional[Region] = None
    risk_level: RiskLevel = RiskLevel.LOW
    previous_failures: int = 0
    successful_payments: int = 0
    preferred_providers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert customer info to dictionary."""
        return {
            "customer_id": self.customer_id,
            "email": self.email,
            "phone": self.phone,
            "country": self.country,
            "region": self.region.value if self.region else None,
            "risk_level": self.risk_level.value,
            "previous_failures": self.previous_failures,
            "successful_payments": self.successful_payments,
            "preferred_providers": self.preferred_providers,
        }


@dataclass
class RoutingDecision:
    """Represents a routing decision with detailed reasoning."""

    selected_provider: str
    strategy_used: str
    decision_factors: Dict[str, Any]
    alternative_providers: List[str]
    confidence_score: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert routing decision to dictionary."""
        return {
            "selected_provider": self.selected_provider,
            "strategy_used": self.strategy_used,
            "decision_factors": self.decision_factors,
            "alternative_providers": self.alternative_providers,
            "confidence_score": self.confidence_score,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Route:
    """Represents a single payment routing attempt with detailed context."""

    provider: str
    attempt_number: int
    status: str
    timestamp: datetime
    reason: Optional[str] = None
    processing_time: Optional[float] = None
    provider_response_code: Optional[str] = None
    provider_message: Optional[str] = None
    network_response_code: Optional[str] = None
    network_latency: Optional[float] = None
    retry_eligible: bool = True
    routing_decision: Optional[RoutingDecision] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert route to dictionary representation."""
        return {
            "provider": self.provider,
            "attempt_number": self.attempt_number,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
            "processing_time": self.processing_time,
            "provider_response_code": self.provider_response_code,
            "provider_message": self.provider_message,
            "network_response_code": self.network_response_code,
            "network_latency": self.network_latency,
            "retry_eligible": self.retry_eligible,
            "routing_decision": (
                self.routing_decision.to_dict() if self.routing_decision else None
            ),
        }


@dataclass
class Transaction:
    """Enhanced transaction with payment context and routing intelligence."""

    id: str
    amount: float
    currency: Currency
    transaction_type: TransactionType
    provider: str
    status: PaymentStatus
    payment_instrument: Optional[PaymentInstrument] = None
    customer_info: Optional[CustomerInfo] = None
    merchant_id: Optional[str] = None
    order_id: Optional[str] = None
    attempts: int = 0
    route_history: List[Route] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    risk_score: Optional[float] = None
    fraud_indicators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary representation."""
        return {
            "id": self.id,
            "amount": self.amount,
            "currency": self.currency.value,
            "transaction_type": self.transaction_type.value,
            "provider": self.provider,
            "status": self.status.value,
            "payment_instrument": (
                self.payment_instrument.to_dict() if self.payment_instrument else None
            ),
            "customer_info": (
                self.customer_info.to_dict() if self.customer_info else None
            ),
            "merchant_id": self.merchant_id,
            "order_id": self.order_id,
            "attempts": self.attempts,
            "route_history": [route.to_dict() for route in self.route_history],
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "risk_score": self.risk_score,
            "fraud_indicators": self.fraud_indicators,
        }


@dataclass
class ProviderCapability:
    """Represents what a provider can handle."""

    supported_networks: List[CardNetwork]
    supported_methods: List[PaymentMethod]
    supported_currencies: List[Currency]
    supported_regions: List[Region]
    min_amount: float
    max_amount: float
    processing_fee: float  # percentage

    def to_dict(self) -> Dict[str, Any]:
        """Convert provider capability to dictionary."""
        return {
            "supported_networks": [n.value for n in self.supported_networks],
            "supported_methods": [m.value for m in self.supported_methods],
            "supported_currencies": [c.value for c in self.supported_currencies],
            "supported_regions": [r.value for r in self.supported_regions],
            "min_amount": self.min_amount,
            "max_amount": self.max_amount,
            "processing_fee": self.processing_fee,
        }


@dataclass
class ProviderHealth:
    """Enhanced provider health with network-specific metrics."""

    provider: str
    success_rate: float
    avg_latency: float
    current_load: int
    is_healthy: bool
    last_checked: datetime
    circuit_breaker_open: bool = False
    circuit_breaker_last_failure: Optional[datetime] = None
    network_success_rates: Dict[str, float] = field(
        default_factory=dict
    )  # Per card network
    method_success_rates: Dict[str, float] = field(
        default_factory=dict
    )  # Per payment method
    region_success_rates: Dict[str, float] = field(default_factory=dict)  # Per region

    def to_dict(self) -> Dict[str, Any]:
        """Convert provider health to dictionary representation."""
        return {
            "provider": self.provider,
            "success_rate": self.success_rate,
            "avg_latency": self.avg_latency,
            "current_load": self.current_load,
            "is_healthy": self.is_healthy,
            "last_checked": self.last_checked.isoformat(),
            "circuit_breaker_open": self.circuit_breaker_open,
            "circuit_breaker_last_failure": (
                self.circuit_breaker_last_failure.isoformat()
                if self.circuit_breaker_last_failure
                else None
            ),
            "network_success_rates": self.network_success_rates,
            "method_success_rates": self.method_success_rates,
            "region_success_rates": self.region_success_rates,
        }


@dataclass
class StructuredLogEntry:
    """Structured log entry for LLM training and analysis."""

    log_id: str
    timestamp: datetime
    level: str  # INFO, WARN, ERROR, DEBUG
    event_type: str
    transaction_id: Optional[str] = None
    provider: Optional[str] = None
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    error_details: Optional[Dict[str, Any]] = None
    routing_context: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, float]] = None
    business_impact: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary for JSON serialization."""
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "event_type": self.event_type,
            "transaction_id": self.transaction_id,
            "provider": self.provider,
            "message": self.message,
            "context": self.context,
            "metrics": self.metrics,
            "error_details": self.error_details,
            "routing_context": self.routing_context,
            "performance_metrics": self.performance_metrics,
            "business_impact": self.business_impact,
        }


@dataclass
class PaymentEvent:
    """Enhanced payment event with structured logging."""

    event_type: str
    transaction: Transaction
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    log_entry: Optional[StructuredLogEntry] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert payment event to dictionary representation."""
        return {
            "event_type": self.event_type,
            "transaction_id": self.transaction.id,
            "provider": self.provider,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "log_entry": self.log_entry.to_dict() if self.log_entry else None,
        }


@dataclass
class RetryConfig:
    """Configuration for payment retry logic."""

    max_attempts: int = 3
    backoff_multiplier: float = 2.0
    initial_delay: float = 1.0
    max_delay: float = 60.0
    retry_on_errors: List[str] = field(
        default_factory=lambda: [
            "TIMEOUT",
            "CONNECTION_REFUSED",
            "NETWORK_TIMEOUT",
            "PROVIDER_MAINTENANCE",
        ]
    )

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        delay = self.initial_delay * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_delay)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    timeout_seconds: int = 30
    half_open_max_calls: int = 3
    min_throughput: int = 10  # Minimum requests before circuit breaker activates
