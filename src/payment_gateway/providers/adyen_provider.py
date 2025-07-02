"""Enhanced Adyen payment provider with global network support."""

from typing import List
from .base import PaymentProvider
from ..core.enums import ErrorCode, CardNetwork, PaymentMethod, Currency, Region
from ..core.models import ProviderCapability


class AdyenProvider(PaymentProvider):
    """Enhanced Adyen provider with strong international support."""

    def __init__(self):
        super().__init__("adyen", success_rate=0.90, avg_latency=150)

    def get_capabilities(self) -> ProviderCapability:
        """Define Adyen's global capabilities."""
        return ProviderCapability(
            supported_networks=[
                CardNetwork.VISA,
                CardNetwork.MASTERCARD,
                CardNetwork.AMEX,
                CardNetwork.DISCOVER,
                CardNetwork.JCB,
                CardNetwork.DINERS,
                CardNetwork.UNIONPAY,
            ],
            supported_methods=[
                PaymentMethod.CARD,
                PaymentMethod.DIGITAL_WALLET,
                PaymentMethod.BANK_TRANSFER,
                PaymentMethod.BUY_NOW_PAY_LATER,
            ],
            supported_currencies=[
                Currency.USD,
                Currency.EUR,
                Currency.GBP,
                Currency.SGD,
                Currency.MYR,
                Currency.THB,
                Currency.IDR,
                Currency.VND,
                Currency.PHP,
            ],
            supported_regions=[
                Region.NORTH_AMERICA,
                Region.EUROPE,
                Region.ASIA_PACIFIC,
                Region.SOUTHEAST_ASIA,
                Region.LATIN_AMERICA,
                Region.MIDDLE_EAST,
            ],
            min_amount=0.01,
            max_amount=1000000.00,
            processing_fee=2.5,  # 2.5% base rate
        )

    def get_network_preference_score(self, network: CardNetwork) -> float:
        """Adyen's strong global network scores."""
        preferences = {
            CardNetwork.VISA: 1.0,  # Excellent global
            CardNetwork.MASTERCARD: 1.0,  # Excellent global
            CardNetwork.AMEX: 0.95,  # Very good
            CardNetwork.DISCOVER: 0.90,  # Good
            CardNetwork.JCB: 0.95,  # Very good (strong Asia presence)
            CardNetwork.DINERS: 0.85,  # Good
            CardNetwork.UNIONPAY: 0.90,  # Good (China focus)
        }
        return preferences.get(network, 0.7)

    def get_specific_errors(self) -> List[ErrorCode]:
        """Adyen-specific error patterns."""
        return [
            ErrorCode.AUTHENTICATION_FAILED,
            ErrorCode.BLOCKED_CARD,
            ErrorCode.TIMEOUT,
            ErrorCode.NETWORK_UNAVAILABLE,
            ErrorCode.ISSUER_UNAVAILABLE,
            ErrorCode.CURRENCY_NOT_SUPPORTED,
        ]
