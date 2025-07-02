"""Custom exceptions for the payment gateway system."""


class PaymentGatewayError(Exception):
    """Base exception for payment gateway errors."""
    pass


class ProviderError(PaymentGatewayError):
    """Exception raised when a payment provider fails."""
    
    def __init__(self, provider: str, message: str, error_code: str = None):
        self.provider = provider
        self.error_code = error_code
        super().__init__(f"Provider {provider}: {message}")


class CircuitBreakerError(PaymentGatewayError):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"Circuit breaker is OPEN for provider {provider}")


class ConfigurationError(PaymentGatewayError):
    """Exception raised for configuration errors."""
    pass


class TransactionNotFoundError(PaymentGatewayError):
    """Exception raised when a transaction is not found."""
    
    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        super().__init__(f"Transaction {transaction_id} not found")


class InvalidProviderError(PaymentGatewayError):
    """Exception raised when an invalid provider is specified."""
    
    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"Invalid provider: {provider}")