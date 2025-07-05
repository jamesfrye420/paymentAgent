"""
Customer data generation for realistic payment simulation.
"""

import random
from typing import List
from faker import Faker

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from payment_gateway.core.models import CustomerInfo
from payment_gateway.core.enums import Region, RiskLevel

from core.config import (REGIONAL_DISTRIBUTION, COUNTRY_MAPPING, RISK_LEVEL_DISTRIBUTION)


class CustomerGenerator:
    """Generates realistic customer data for payment simulation."""
    
    def __init__(self):
        """Initialize the customer generator."""
        self.fake = Faker()
    
    def generate_customer_pool(self, count: int) -> List[CustomerInfo]:
        """Generate a pool of realistic customers."""
        customers = []
        
        for _ in range(count):
            customer = self._generate_single_customer()
            customers.append(customer)
        
        return customers
    
    def _generate_single_customer(self) -> CustomerInfo:
        """Generate a single realistic customer."""
        # Select region based on weights
        region_name, region_enum = self._select_region()
        
        # Select country based on region
        country = self._select_country(region_name)
        
        # Select risk level based on realistic distribution
        risk_level = self._select_risk_level()
        
        # Generate transaction history based on risk level
        successful_payments, previous_failures = self._generate_transaction_history(risk_level)
        
        # Generate preferred providers
        preferred_providers = self._generate_preferred_providers(region_enum, risk_level)
        
        return CustomerInfo(
            customer_id=f"cust_{self.fake.uuid4()[:8]}",
            email=self.fake.email(),
            phone=self.fake.phone_number(),
            country=country,
            region=region_enum,
            risk_level=risk_level,
            successful_payments=successful_payments,
            previous_failures=previous_failures,
            preferred_providers=preferred_providers
        )
    
    def _select_region(self) -> tuple:
        """Select a region based on realistic distribution."""
        region_names = [r[0] for r in REGIONAL_DISTRIBUTION]
        weights = [r[1] for r in REGIONAL_DISTRIBUTION]
        
        region_name = random.choices(region_names, weights=weights)[0]
        region_enum = Region[region_name]
        
        return region_name, region_enum
    
    def _select_country(self, region_name: str) -> str:
        """Select a country based on the region."""
        countries = COUNTRY_MAPPING.get(region_name, ['US'])
        return random.choice(countries)
    
    def _select_risk_level(self) -> RiskLevel:
        """Select risk level based on realistic distribution."""
        risk_names = [r[0] for r in RISK_LEVEL_DISTRIBUTION]
        weights = [r[1] for r in RISK_LEVEL_DISTRIBUTION]
        
        risk_name = random.choices(risk_names, weights=weights)[0]
        return RiskLevel[risk_name]
    
    def _generate_transaction_history(self, risk_level: RiskLevel) -> tuple:
        """Generate realistic transaction history based on risk level."""
        if risk_level == RiskLevel.LOW:
            successful_payments = random.randint(50, 200)
            previous_failures = random.randint(0, 2)
        elif risk_level == RiskLevel.MEDIUM:
            successful_payments = random.randint(10, 100)
            previous_failures = random.randint(1, 5)
        else:  # HIGH risk
            successful_payments = random.randint(0, 20)
            previous_failures = random.randint(3, 15)
        
        return successful_payments, previous_failures
    
    def _generate_preferred_providers(self, region: Region, risk_level: RiskLevel) -> List[str]:
        """Generate preferred payment providers based on region and risk."""
        all_providers = ['stripe', 'adyen', 'paypal', 'razorpay']
        
        # Regional preferences
        regional_preferences = {
            Region.NORTH_AMERICA: ['stripe', 'paypal'],
            Region.EUROPE: ['adyen', 'stripe'],
            Region.SOUTHEAST_ASIA: ['razorpay', 'adyen'],
            Region.ASIA_PACIFIC: ['adyen', 'stripe'],
            Region.LATIN_AMERICA: ['stripe', 'paypal']
        }
        
        preferred = regional_preferences.get(region, ['stripe', 'adyen'])
        
        # High-risk customers might have fewer preferred providers
        if risk_level == RiskLevel.HIGH:
            return random.sample(preferred, k=1)
        else:
            # Add one more provider for variety
            other_providers = [p for p in all_providers if p not in preferred]
            if other_providers:
                preferred.extend(random.sample(other_providers, k=1))
            
            return random.sample(preferred, k=random.randint(1, len(preferred)))
    
    def generate_customer_for_merchant_type(self, merchant_type: str) -> CustomerInfo:
        """Generate a customer specifically for a merchant type."""
        # Different customer profiles for different Grab services
        customer_profiles = {
            'transport': {
                'regions': [Region.SOUTHEAST_ASIA, Region.ASIA_PACIFIC],
                'risk_weights': [(RiskLevel.LOW, 0.8), (RiskLevel.MEDIUM, 0.2)],
                'age_range': (18, 65)
            },
            'food_delivery': {
                'regions': [Region.NORTH_AMERICA, Region.EUROPE, Region.SOUTHEAST_ASIA],
                'risk_weights': [(RiskLevel.LOW, 0.7), (RiskLevel.MEDIUM, 0.3)],
                'age_range': (18, 45)
            },
            'mart_grocery': {
                'regions': [Region.SOUTHEAST_ASIA, Region.NORTH_AMERICA],
                'risk_weights': [(RiskLevel.LOW, 0.9), (RiskLevel.MEDIUM, 0.1)],
                'age_range': (25, 60)
            },
            'express_delivery': {
                'regions': [Region.SOUTHEAST_ASIA, Region.ASIA_PACIFIC],
                'risk_weights': [(RiskLevel.LOW, 0.6), (RiskLevel.MEDIUM, 0.35), (RiskLevel.HIGH, 0.05)],
                'age_range': (20, 50)
            },
            'financial_services': {
                'regions': [Region.SOUTHEAST_ASIA],
                'risk_weights': [(RiskLevel.LOW, 0.5), (RiskLevel.MEDIUM, 0.4), (RiskLevel.HIGH, 0.1)],
                'age_range': (25, 65)
            }
        }
        
        profile = customer_profiles.get(merchant_type, customer_profiles['transport'])
        
        # Select region from preferred regions
        region = random.choice(profile['regions'])
        
        # Select risk level based on profile
        risk_levels = [r[0] for r in profile['risk_weights']]
        weights = [r[1] for r in profile['risk_weights']]
        risk_level = random.choices(risk_levels, weights=weights)[0]
        
        # Generate customer with profile-specific characteristics
        region_name = region.name
        country = self._select_country(region_name)
        successful_payments, previous_failures = self._generate_transaction_history(risk_level)
        preferred_providers = self._generate_preferred_providers(region, risk_level)
        
        return CustomerInfo(
            customer_id=f"cust_{merchant_type}_{self.fake.uuid4()[:8]}",
            email=self.fake.email(),
            phone=self.fake.phone_number(),
            country=country,
            region=region,
            risk_level=risk_level,
            successful_payments=successful_payments,
            previous_failures=previous_failures,
            preferred_providers=preferred_providers
        )