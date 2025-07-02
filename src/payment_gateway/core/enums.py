"""Core enumerations for the payment gateway system."""

from enum import Enum


class PaymentStatus(Enum):
    """Payment transaction status enumeration."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ErrorCode(Enum):
    """Error codes for various payment failure scenarios."""
    
    # Network errors
    TIMEOUT = "TIMEOUT"
    CONNECTION_REFUSED = "CONNECTION_REFUSED"
    SSL_HANDSHAKE_FAILED = "SSL_HANDSHAKE_FAILED"
    DNS_RESOLUTION_FAILED = "DNS_RESOLUTION_FAILED"
    
    # Provider-specific errors
    CARD_DECLINED = "CARD_DECLINED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    BLOCKED_CARD = "BLOCKED_CARD"
    ACCOUNT_RESTRICTED = "ACCOUNT_RESTRICTED"
    CURRENCY_NOT_SUPPORTED = "CURRENCY_NOT_SUPPORTED"
    REGION_BLOCKED = "REGION_BLOCKED"
    COMPLIANCE_VIOLATION = "COMPLIANCE_VIOLATION"
    
    # Card network specific errors
    NETWORK_UNAVAILABLE = "NETWORK_UNAVAILABLE"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    ISSUER_UNAVAILABLE = "ISSUER_UNAVAILABLE"
    INVALID_CARD_NUMBER = "INVALID_CARD_NUMBER"
    EXPIRED_CARD = "EXPIRED_CARD"
    INVALID_CVV = "INVALID_CVV"
    
    # Payment method specific errors
    WALLET_INSUFFICIENT_BALANCE = "WALLET_INSUFFICIENT_BALANCE"
    WALLET_SUSPENDED = "WALLET_SUSPENDED"
    BANK_ACCOUNT_CLOSED = "BANK_ACCOUNT_CLOSED"
    BANK_TRANSFER_LIMIT_EXCEEDED = "BANK_TRANSFER_LIMIT_EXCEEDED"
    
    # System errors
    RATE_LIMITED = "RATE_LIMITED"
    PROVIDER_MAINTENANCE = "PROVIDER_MAINTENANCE"
    FRAUD_DETECTED = "FRAUD_DETECTED"
    DUPLICATE_TRANSACTION = "DUPLICATE_TRANSACTION"


class CircuitBreakerState(Enum):
    """Circuit breaker state enumeration."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class RoutingStrategy(Enum):
    """Payment routing strategy enumeration."""
    HEALTH_BASED = "health_based"
    ROUND_ROBIN = "round_robin"
    FAILOVER = "failover"
    COST_OPTIMIZED = "cost_optimized"
    CARD_NETWORK_OPTIMIZED = "card_network_optimized"


class CardNetwork(Enum):
    """Card network enumeration."""
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    JCB = "jcb"
    DINERS = "diners"
    UNIONPAY = "unionpay"


class PaymentMethod(Enum):
    """Payment method enumeration."""
    CARD = "card"
    DIGITAL_WALLET = "digital_wallet"
    BANK_TRANSFER = "bank_transfer"
    CRYPTOCURRENCY = "cryptocurrency"
    BUY_NOW_PAY_LATER = "buy_now_pay_later"


class Currency(Enum):
    """Supported currencies."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    SGD = "SGD"
    MYR = "MYR"
    THB = "THB"
    IDR = "IDR"
    VND = "VND"
    PHP = "PHP"


class TransactionType(Enum):
    """Transaction type enumeration."""
    PAYMENT = "payment"
    REFUND = "refund"
    AUTHORIZATION = "authorization"
    CAPTURE = "capture"
    VOID = "void"


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Region(Enum):
    """Geographic regions."""
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    SOUTHEAST_ASIA = "southeast_asia"
    LATIN_AMERICA = "latin_america"
    MIDDLE_EAST = "middle_east"
    AFRICA = "africa"