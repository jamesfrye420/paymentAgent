from typing import List
from .base import PaymentProvider
from ..core.enums import ErrorCode, CardNetwork, PaymentMethod, Currency, Region
from ..core.models import ProviderCapability


class PayPalProvider(PaymentProvider):
    """Enhanced PayPal provider with wallet and credit specialization."""
    
    def __init__(self):
        super().__init__("paypal", success_rate=0.80, avg_latency=300)
    
    def get_capabilities(self) -> ProviderCapability:
        """Define PayPal's wallet-focused capabilities."""
        return ProviderCapability(
            supported_networks=[
                CardNetwork.VISA,
                CardNetwork.MASTERCARD,
                CardNetwork.AMEX,
                CardNetwork.DISCOVER
            ],
            supported_methods=[
                PaymentMethod.DIGITAL_WALLET,
                PaymentMethod.CARD,
                PaymentMethod.BANK_TRANSFER,
                PaymentMethod.BUY_NOW_PAY_LATER
            ],
            supported_currencies=[
                Currency.USD, Currency.EUR, Currency.GBP,
                Currency.SGD, Currency.MYR, Currency.THB
            ],
            supported_regions=[
                Region.NORTH_AMERICA,
                Region.EUROPE,
                Region.ASIA_PACIFIC,
                Region.SOUTHEAST_ASIA,
                Region.LATIN_AMERICA
            ],
            min_amount=1.00,
            max_amount=60000.00,
            processing_fee=3.49  # Higher fee but good conversion
        )
    
    def get_network_preference_score(self, network: CardNetwork) -> float:
        """PayPal's network preferences (wallet-first approach)."""
        preferences = {
            CardNetwork.VISA: 0.95,       # Very good
            CardNetwork.MASTERCARD: 0.95, # Very good
            CardNetwork.AMEX: 0.90,       # Good
            CardNetwork.DISCOVER: 0.85,   # OK
            CardNetwork.JCB: 0.70,        # Limited
            CardNetwork.DINERS: 0.60,     # Poor
            CardNetwork.UNIONPAY: 0.50    # Very limited
        }
        return preferences.get(network, 0.4)
    
    def get_specific_errors(self) -> List[ErrorCode]:
        """PayPal-specific error patterns."""
        return [
            ErrorCode.ACCOUNT_RESTRICTED,
            ErrorCode.CURRENCY_NOT_SUPPORTED,
            ErrorCode.TIMEOUT,
            ErrorCode.WALLET_INSUFFICIENT_BALANCE,
            ErrorCode.WALLET_SUSPENDED,
            ErrorCode.FRAUD_DETECTED
        ]