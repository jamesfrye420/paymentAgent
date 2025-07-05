"""
Payment instrument generation for realistic payment simulation.
"""

import random
from typing import Dict, Any
from faker import Faker
from faker.providers import credit_card

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from payment_gateway.core.models import PaymentInstrument, CustomerInfo
from payment_gateway.core.enums import PaymentMethod, CardNetwork, Currency
from core.config import (
    PAYMENT_METHOD_PREFERENCES, CARD_NETWORK_PREFERENCES, 
    CARD_ISSUERS, WALLET_PREFERENCES, PRIMARY_CURRENCIES, LOCAL_CURRENCIES
)


class PaymentInstrumentGenerator:
    """Generates realistic payment instruments for simulation."""
    
    def __init__(self):
        """Initialize the payment instrument generator."""
        self.fake = Faker()
        self.fake.add_provider(credit_card)
    
    def generate_realistic_payment_instrument(self, customer: CustomerInfo) -> PaymentInstrument:
        """Generate realistic payment instrument based on customer region."""
        region_name = customer.region.name
        
        # Get payment method preferences for the region
        preferences = PAYMENT_METHOD_PREFERENCES.get(region_name, 
                                                    PAYMENT_METHOD_PREFERENCES['NORTH_AMERICA'])
        
        methods = [PaymentMethod[p[0]] for p in preferences]
        weights = [p[1] for p in preferences]
        payment_method = random.choices(methods, weights=weights)[0]
        
        if payment_method == PaymentMethod.CARD:
            return self._generate_card_instrument(customer)
        elif payment_method == PaymentMethod.DIGITAL_WALLET:
            return self._generate_wallet_instrument(customer)
        elif payment_method == PaymentMethod.BANK_TRANSFER:
            return self._generate_bank_instrument(customer)
        else:
            return self._generate_bnpl_instrument(customer)
    
    def _generate_card_instrument(self, customer: CustomerInfo) -> PaymentInstrument:
        """Generate realistic card payment instrument."""
        region_name = customer.region.name
        
        # Get card network preferences for the region
        preferences = CARD_NETWORK_PREFERENCES.get(region_name, 
                                                CARD_NETWORK_PREFERENCES['NORTH_AMERICA'])
        
        networks = [CardNetwork[p[0]] for p in preferences]
        weights = [p[1] for p in preferences]
        network = random.choices(networks, weights=weights)[0]
        
        # Generate card details
        card_number = self._generate_card_number(network)
        
        return PaymentInstrument(
            method=PaymentMethod.CARD,
            network=network,
            last_four=card_number[-4:],
            expiry_month=random.randint(1, 12),
            expiry_year=random.randint(2024, 2030),
            country_code=customer.country,
            issuer=self._get_realistic_issuer(customer.country, network),
            brand=self._get_card_brand(network)
        )
    
    def _generate_card_number(self, network: CardNetwork) -> str:
        """Generate realistic card number for the network."""
        # Use faker's credit card generation with network mapping
        network_mapping = {
            CardNetwork.VISA: 'visa',
            CardNetwork.MASTERCARD: 'mastercard',
            CardNetwork.AMEX: 'amex',
            CardNetwork.DISCOVER: 'discover',
            CardNetwork.JCB: 'jcb',
            CardNetwork.DINERS: 'diners',
            CardNetwork.UNIONPAY: 'visa'  # Faker doesn't have UnionPay, use Visa format
        }
        
        card_type = network_mapping.get(network, 'visa')
        try:
            return self.fake.credit_card_number(card_type=card_type)
        except:
            # Fallback to visa if card type not supported
            return self.fake.credit_card_number(card_type='visa')
    
    def _get_card_brand(self, network: CardNetwork) -> str:
        """Get realistic card brand (credit/debit) based on network."""
        # Different networks have different credit/debit distributions
        credit_probability = {
            CardNetwork.VISA: 0.6,
            CardNetwork.MASTERCARD: 0.65,
            CardNetwork.AMEX: 0.95,  # Amex is mostly credit
            CardNetwork.DISCOVER: 0.7,
            CardNetwork.JCB: 0.8,
            CardNetwork.DINERS: 0.9,
            CardNetwork.UNIONPAY: 0.4   # UnionPay is often debit in China
        }
        
        prob = credit_probability.get(network, 0.6)
        card_type = 'credit' if random.random() < prob else 'debit'
        
        return f"{network.value.lower()}_{card_type}"
    
    def _generate_wallet_instrument(self, customer: CustomerInfo) -> PaymentInstrument:
        """Generate digital wallet payment instrument."""
        region_name = customer.region.name
        
        wallets = WALLET_PREFERENCES.get(region_name, ['apple_pay', 'google_pay'])
        wallet_type = random.choice(wallets)
        
        return PaymentInstrument(
            method=PaymentMethod.DIGITAL_WALLET,
            network=None,  # Digital wallets don't have card networks
            last_four=None,  # No card number for wallets
            expiry_month=None,  # No expiry for wallets
            expiry_year=None,  # No expiry for wallets
            wallet_type=wallet_type,
            country_code=customer.country,
            issuer=self._get_wallet_issuer(wallet_type),  # Add wallet issuer
            brand=wallet_type  # Use wallet type as brand
        )
    
    def _get_wallet_issuer(self, wallet_type: str) -> str:
        """Get issuer for digital wallet."""
        wallet_issuers = {
            'apple_pay': 'Apple Inc.',
            'google_pay': 'Google LLC',
            'samsung_pay': 'Samsung Electronics',
            'grab_pay': 'Grab Holdings',
            'paym': 'Pay Digital',
            'alipay': 'Ant Group',
            'wechat_pay': 'Tencent'
        }
        return wallet_issuers.get(wallet_type, 'Digital Wallet Provider')
    
    def _generate_bank_instrument(self, customer: CustomerInfo) -> PaymentInstrument:
        """Generate bank transfer payment instrument."""
        return PaymentInstrument(
            method=PaymentMethod.BANK_TRANSFER,
            country_code=customer.country,
            issuer=self._get_realistic_bank(customer.country)
        )
    
    def _generate_bnpl_instrument(self, customer: CustomerInfo) -> PaymentInstrument:
        """Generate Buy Now Pay Later payment instrument."""
        # BNPL providers by region
        bnpl_providers = {
            'NORTH_AMERICA': ['klarna', 'afterpay', 'affirm', 'sezzle'],
            'EUROPE': ['klarna', 'clearpay', 'paypal_pay_in_4'],
            'SOUTHEAST_ASIA': ['atome', 'grab_paylater', 'shopee_paylater'],
            'ASIA_PACIFIC': ['afterpay', 'zip', 'klarna'],
            'LATIN_AMERICA': ['mercado_credito', 'addi', 'kueski']
        }
        
        region_name = customer.region.name
        providers = bnpl_providers.get(region_name, ['klarna', 'afterpay'])
        
        return PaymentInstrument(
            method=PaymentMethod.BUY_NOW_PAY_LATER,
            country_code=customer.country,
            brand=random.choice(providers)
        )
    
    def _get_realistic_issuer(self, country: str, network: CardNetwork) -> str:
        """Get realistic card issuer by country and network."""
        country_issuers = CARD_ISSUERS.get(country, ['Generic Bank', 'Local Bank'])
        return random.choice(country_issuers)
    
    def _get_realistic_bank(self, country: str) -> str:
        """Get realistic bank name for bank transfers."""
        country_issuers = CARD_ISSUERS.get(country, ['Generic Bank', 'Local Bank'])
        bank_name = random.choice(country_issuers)
        
        # Add "Bank" suffix if not already present
        if not bank_name.lower().endswith('bank'):
            bank_name += ' Bank'
        
        return bank_name
    
    def generate_currency_for_transaction(self, customer: CustomerInfo, 
                                        merchant: Dict[str, Any]) -> Currency:
        """Select realistic currency for transaction."""
        region_name = customer.region.name
        
        # 80% chance of using local currency, 20% chance of international
        if random.random() < 0.8:
            # Try local currency first
            local_currency_str = LOCAL_CURRENCIES.get(customer.country)
            if local_currency_str:
                try:
                    return Currency[local_currency_str]
                except KeyError:
                    pass
            
            # Fallback to regional primary currency
            primary_currency_str = PRIMARY_CURRENCIES.get(region_name, 'USD')
            try:
                return Currency[primary_currency_str]
            except KeyError:
                return Currency.USD
        else:
            # International transaction - use USD or EUR
            return random.choice([Currency.USD, Currency.EUR])
    
    def generate_payment_for_merchant_type(self, customer: CustomerInfo, 
                                         merchant_type: str) -> PaymentInstrument:
        """Generate payment instrument optimized for specific merchant type."""
        # Different merchant types prefer different payment methods
        method_preferences = {
            'transport': [
                (PaymentMethod.DIGITAL_WALLET, 0.5),  # Quick mobile payments
                (PaymentMethod.CARD, 0.5)
            ],
            'food_delivery': [
                (PaymentMethod.DIGITAL_WALLET, 0.4),
                (PaymentMethod.CARD, 0.6)
            ],
            'mart_grocery': [
                (PaymentMethod.CARD, 0.5),
                (PaymentMethod.DIGITAL_WALLET, 0.3),
                (PaymentMethod.BANK_TRANSFER, 0.2)
            ],
            'express_delivery': [
                (PaymentMethod.CARD, 0.6),
                (PaymentMethod.DIGITAL_WALLET, 0.4)
            ],
            'financial_services': [
                (PaymentMethod.BANK_TRANSFER, 0.6),
                (PaymentMethod.CARD, 0.4)
            ],
            'rewards_partners': [
                (PaymentMethod.CARD, 0.7),
                (PaymentMethod.DIGITAL_WALLET, 0.3)
            ],
            'enterprise_b2b': [
                (PaymentMethod.BANK_TRANSFER, 0.8),
                (PaymentMethod.CARD, 0.2)
            ]
        }
        
        preferences = method_preferences.get(merchant_type, 
                                           [(PaymentMethod.CARD, 0.6), (PaymentMethod.DIGITAL_WALLET, 0.4)])
        
        methods = [p[0] for p in preferences]
        weights = [p[1] for p in preferences]
        payment_method = random.choices(methods, weights=weights)[0]
        
        # Generate instrument based on selected method
        if payment_method == PaymentMethod.CARD:
            return self._generate_card_instrument(customer)
        elif payment_method == PaymentMethod.DIGITAL_WALLET:
            return self._generate_wallet_instrument(customer)
        elif payment_method == PaymentMethod.BANK_TRANSFER:
            return self._generate_bank_instrument(customer)
        else:
            return self._generate_bnpl_instrument(customer)
    
    def generate_high_value_payment_instrument(self, customer: CustomerInfo) -> PaymentInstrument:
        """Generate payment instrument suitable for high-value transactions."""
        # High-value transactions prefer more secure methods
        if customer.risk_level.name == 'LOW' and customer.successful_payments > 50:
            # Trusted customers can use any method
            if random.random() < 0.6:
                return self._generate_card_instrument(customer)
            else:
                return self._generate_bank_instrument(customer)
        else:
            # New or risky customers limited to cards for better fraud protection
            return self._generate_card_instrument(customer)
    
    def generate_fraud_prone_instrument(self, customer: CustomerInfo) -> PaymentInstrument:
        """Generate payment instrument that might be more prone to fraud (for testing)."""
        # Generate cards from higher-risk scenarios
        instrument = self._generate_card_instrument(customer)
        
        # Make it more fraud-prone by adjusting characteristics
        if random.random() < 0.3:
            # Expired card
            instrument.expiry_year = random.randint(2020, 2023)
        
        if random.random() < 0.2:
            # International card for domestic transaction
            instrument.country_code = random.choice(['US', 'GB', 'DE']) if customer.country in ['SG', 'MY', 'TH'] else 'SG'
        
        return instrument