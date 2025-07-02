"""Enhanced Stripe payment provider with card network support."""

from typing import List
from .base import PaymentProvider
from ..core.enums import ErrorCode, CardNetwork, PaymentMethod, Currency, Region
from ..core.models import ProviderCapability


class StripeProvider(PaymentProvider):
    """Enhanced Stripe provider with network preferences and capabilities."""

    def __init__(self):
        super().__init__("stripe", success_rate=0.85, avg_latency=200)

    def get_capabilities(self) -> ProviderCapability:
        """Define Stripe's capabilities."""
        return ProviderCapability(
            supported_networks=[
                CardNetwork.VISA,
                CardNetwork.MASTERCARD,
                CardNetwork.AMEX,
                CardNetwork.DISCOVER,
                CardNetwork.JCB,
            ],
            supported_methods=[
                PaymentMethod.CARD,
                PaymentMethod.DIGITAL_WALLET,
                PaymentMethod.BANK_TRANSFER,
            ],
            supported_currencies=[
                Currency.USD,
                Currency.EUR,
                Currency.GBP,
                Currency.SGD,
                Currency.MYR,
            ],
            supported_regions=[
                Region.NORTH_AMERICA,
                Region.EUROPE,
                Region.ASIA_PACIFIC,
                Region.SOUTHEAST_ASIA,
            ],
            min_amount=0.50,
            max_amount=999999.99,
            processing_fee=2.9,  # 2.9%
        )

    def get_network_preference_score(self, network: CardNetwork) -> float:
        """Stripe's network preference scores."""
        preferences = {
            CardNetwork.VISA: 1.0,  # Excellent
            CardNetwork.MASTERCARD: 0.98,  # Very good
            CardNetwork.AMEX: 0.85,  # Good but higher fees
            CardNetwork.DISCOVER: 0.95,  # Good
            CardNetwork.JCB: 0.80,  # OK, some regional issues
            CardNetwork.DINERS: 0.70,  # Limited support
            CardNetwork.UNIONPAY: 0.60,  # Limited support
        }
        return preferences.get(network, 0.5)

    def get_specific_errors(self) -> List[ErrorCode]:
        """Stripe-specific error patterns."""
        return [
            ErrorCode.CARD_DECLINED,
            ErrorCode.INSUFFICIENT_FUNDS,
            ErrorCode.TIMEOUT,
            ErrorCode.INVALID_CARD_NUMBER,
            ErrorCode.EXPIRED_CARD,
            ErrorCode.INVALID_CVV,
            ErrorCode.FRAUD_DETECTED,
        ]
