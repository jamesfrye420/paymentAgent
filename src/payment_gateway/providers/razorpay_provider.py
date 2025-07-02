"""Enhanced Razorpay provider with Southeast Asia focus."""

from typing import List
from .base import PaymentProvider
from ..core.enums import ErrorCode, CardNetwork, PaymentMethod, Currency, Region
from ..core.models import ProviderCapability


class RazorpayProvider(PaymentProvider):
    """Enhanced Razorpay provider optimized for Southeast Asian markets."""

    def __init__(self):
        super().__init__("razorpay", success_rate=0.88, avg_latency=180)

    def get_capabilities(self) -> ProviderCapability:
        """Define Razorpay's Southeast Asia focused capabilities."""
        return ProviderCapability(
            supported_networks=[
                CardNetwork.VISA,
                CardNetwork.MASTERCARD,
                CardNetwork.AMEX,
                CardNetwork.JCB,
                CardNetwork.UNIONPAY,
            ],
            supported_methods=[
                PaymentMethod.CARD,
                PaymentMethod.DIGITAL_WALLET,
                PaymentMethod.BANK_TRANSFER,
                PaymentMethod.BUY_NOW_PAY_LATER,
            ],
            supported_currencies=[
                Currency.SGD,
                Currency.MYR,
                Currency.THB,
                Currency.IDR,
                Currency.VND,
                Currency.PHP,
                Currency.USD,
                Currency.EUR,
            ],
            supported_regions=[
                Region.SOUTHEAST_ASIA,
                Region.ASIA_PACIFIC,
                Region.NORTH_AMERICA,
                Region.EUROPE,
            ],
            min_amount=0.10,
            max_amount=500000.00,
            processing_fee=2.0,  # Competitive local rates
        )

    def get_network_preference_score(self, network: CardNetwork) -> float:
        """Razorpay's network preferences for SEA markets."""
        preferences = {
            CardNetwork.VISA: 0.98,  # Excellent in SEA
            CardNetwork.MASTERCARD: 0.96,  # Very good in SEA
            CardNetwork.UNIONPAY: 0.92,  # Strong for Chinese tourists
            CardNetwork.JCB: 0.90,  # Good for Japanese market
            CardNetwork.AMEX: 0.75,  # Limited acceptance
            CardNetwork.DISCOVER: 0.70,  # Poor in SEA
            CardNetwork.DINERS: 0.65,  # Very limited
        }
        return preferences.get(network, 0.5)

    def get_specific_errors(self) -> List[ErrorCode]:
        """Razorpay-specific error patterns."""
        return [
            ErrorCode.REGION_BLOCKED,
            ErrorCode.COMPLIANCE_VIOLATION,
            ErrorCode.TIMEOUT,
            ErrorCode.CURRENCY_NOT_SUPPORTED,
            ErrorCode.BANK_TRANSFER_LIMIT_EXCEEDED,
            ErrorCode.NETWORK_TIMEOUT,
        ]
