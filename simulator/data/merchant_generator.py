"""
Merchant data generation for realistic payment simulation.
"""

import random
from typing import List, Dict, Any
from faker import Faker

from core.config import (
    GRAB_MERCHANT_TYPES, GRAB_TRANSACTION_AMOUNTS, GRAB_PEAK_HOURS
)


class MerchantGenerator:
    """Generates realistic merchant data for Grab ecosystem simulation."""
    
    def __init__(self):
        """Initialize the merchant generator."""
        self.fake = Faker()
    
    def generate_merchant_pool(self, count: int) -> List[Dict[str, Any]]:
        """Generate a pool of realistic Grab ecosystem merchants."""
        merchants = []
        
        for _ in range(count):
            merchant = self._generate_single_merchant()
            merchants.append(merchant)
        
        return merchants
    
    def _generate_single_merchant(self) -> Dict[str, Any]:
        """Generate a single realistic merchant."""
        # Select merchant type based on Grab ecosystem weights
        merchant_types = [m[0] for m in GRAB_MERCHANT_TYPES]
        weights = [m[1] for m in GRAB_MERCHANT_TYPES]
        merchant_type = random.choices(merchant_types, weights=weights)[0]
        
        # Generate merchant based on type
        return {
            'merchant_id': f"merch_{merchant_type}_{self.fake.uuid4()[:8]}",
            'name': self._generate_merchant_name(merchant_type),
            'type': merchant_type,
            'country': self._select_merchant_country(merchant_type),
            'avg_transaction_value': self._get_avg_transaction_amount(merchant_type),
            'peak_hours': self._get_peak_hours(merchant_type),
            'business_model': self._get_business_model(merchant_type),
            'commission_rate': self._get_commission_rate(merchant_type),
            'volume_tier': self._get_volume_tier(merchant_type)
        }
    
    def _generate_merchant_name(self, merchant_type: str) -> str:
        """Generate realistic merchant names by type."""
        name_patterns = {
            'transport': [
                f"Grab {self.fake.city()} Transport",
                f"{self.fake.city()} Ride Services",
                f"Metro {self.fake.city()} Taxi"
            ],
            'food_delivery': [
                f"{self.fake.company()} Restaurant",
                f"{self.fake.first_name()}'s Kitchen",
                f"{self.fake.city()} Food Hub",
                f"Quick Bite {self.fake.city()}",
                f"{self.fake.last_name()} Cafe"
            ],
            'mart_grocery': [
                f"{self.fake.city()} Mart",
                f"Fresh Market {self.fake.city()}",
                f"{self.fake.company()} Grocery",
                f"Daily Essentials {self.fake.city()}"
            ],
            'express_delivery': [
                f"Express {self.fake.city()}",
                f"Quick Courier {self.fake.city()}",
                f"{self.fake.company()} Logistics"
            ],
            'financial_services': [
                f"Grab {self.fake.city()} Finance",
                f"{self.fake.city()} Digital Bank",
                f"Quick Loan {self.fake.city()}"
            ],
            'rewards_partners': [
                f"{self.fake.company()} Store",
                f"{self.fake.city()} Mall",
                f"Premium {self.fake.company()}"
            ],
            'enterprise_b2b': [
                f"{self.fake.company()} Corp",
                f"Business Solutions {self.fake.city()}",
                f"{self.fake.company()} Enterprise"
            ]
        }
        
        patterns = name_patterns.get(merchant_type, [self.fake.company()])
        return random.choice(patterns)
    
    def _select_merchant_country(self, merchant_type: str) -> str:
        """Select merchant country based on type and Grab's presence."""
        # Grab operates primarily in Southeast Asia
        grab_countries = ['SG', 'MY', 'TH', 'ID', 'VN', 'PH']
        
        # Some services have broader reach
        if merchant_type in ['financial_services', 'enterprise_b2b']:
            # These might have regional presence
            extended_countries = grab_countries + ['US', 'AU', 'JP']
            return random.choice(extended_countries)
        elif merchant_type == 'rewards_partners':
            # Global partners might be anywhere
            return random.choice(['SG', 'MY', 'TH', 'ID', 'VN', 'PH', 'US', 'GB', 'AU'])
        else:
            # Core services stay in SEA
            return random.choice(grab_countries)
    
    def _get_avg_transaction_amount(self, merchant_type: str) -> float:
        """Get realistic average transaction amounts for Grab merchant types."""
        min_amt, max_amt = GRAB_TRANSACTION_AMOUNTS.get(merchant_type, (10, 50))
        return random.uniform(min_amt, max_amt)
    
    def _get_peak_hours(self, merchant_type: str) -> tuple:
        """Get peak hours for Grab merchant types."""
        return GRAB_PEAK_HOURS.get(merchant_type, (9, 17))
    
    def _get_business_model(self, merchant_type: str) -> str:
        """Get business model characteristics."""
        models = {
            'transport': 'commission_per_ride',
            'food_delivery': 'commission_per_order',
            'mart_grocery': 'commission_per_order',
            'express_delivery': 'commission_per_delivery',
            'financial_services': 'transaction_fee',
            'rewards_partners': 'revenue_share',
            'enterprise_b2b': 'subscription_fee'
        }
        return models.get(merchant_type, 'commission_based')
    
    def _get_commission_rate(self, merchant_type: str) -> float:
        """Get typical commission rates by merchant type."""
        rates = {
            'transport': random.uniform(0.15, 0.25),      # 15-25%
            'food_delivery': random.uniform(0.20, 0.30),  # 20-30%
            'mart_grocery': random.uniform(0.10, 0.20),   # 10-20%
            'express_delivery': random.uniform(0.15, 0.25), # 15-25%
            'financial_services': random.uniform(0.02, 0.05), # 2-5%
            'rewards_partners': random.uniform(0.05, 0.15), # 5-15%
            'enterprise_b2b': random.uniform(0.10, 0.20)  # 10-20%
        }
        return rates.get(merchant_type, 0.15)
    
    def _get_volume_tier(self, merchant_type: str) -> str:
        """Get volume tier based on merchant type."""
        # Different services have different typical volumes
        tier_weights = {
            'transport': [('high', 0.6), ('medium', 0.3), ('low', 0.1)],
            'food_delivery': [('high', 0.4), ('medium', 0.4), ('low', 0.2)],
            'mart_grocery': [('medium', 0.5), ('high', 0.3), ('low', 0.2)],
            'express_delivery': [('medium', 0.6), ('high', 0.2), ('low', 0.2)],
            'financial_services': [('high', 0.8), ('medium', 0.2)],
            'rewards_partners': [('low', 0.4), ('medium', 0.4), ('high', 0.2)],
            'enterprise_b2b': [('high', 0.7), ('medium', 0.3)]
        }
        
        weights = tier_weights.get(merchant_type, [('medium', 0.6), ('high', 0.2), ('low', 0.2)])
        tiers = [w[0] for w in weights]
        tier_weights_only = [w[1] for w in weights]
        
        return random.choices(tiers, weights=tier_weights_only)[0]
    
    def generate_merchant_for_time(self, hour: int) -> Dict[str, Any]:
        """Generate a merchant that's likely to be active at this hour."""
        # Find merchant types that are active at this hour
        active_types = []
        for merchant_type, _ in GRAB_MERCHANT_TYPES:
            peak_start, peak_end = GRAB_PEAK_HOURS.get(merchant_type, (9, 17))
            
            # Check if current hour is within peak or extended hours
            if peak_start <= hour <= peak_end:
                active_types.append(merchant_type)
            elif merchant_type in ['transport', 'food_delivery']:
                # These services have extended hours
                if hour >= 6 and hour <= 23:  # 6 AM to 11 PM
                    active_types.append(merchant_type)
        
        if not active_types:
            # Default to transport (24/7 service)
            active_types = ['transport']
        
        # Select from active types
        selected_type = random.choice(active_types)
        
        # Generate merchant of selected type
        merchant = self._generate_single_merchant()
        merchant['type'] = selected_type
        merchant['name'] = self._generate_merchant_name(selected_type)
        merchant['avg_transaction_value'] = self._get_avg_transaction_amount(selected_type)
        merchant['peak_hours'] = self._get_peak_hours(selected_type)
        
        return merchant
    
    def get_merchant_activity_multiplier(self, merchant: Dict[str, Any], hour: int) -> float:
        """Get activity multiplier for a merchant at a specific hour."""
        peak_start, peak_end = merchant['peak_hours']
        
        if peak_start <= hour <= peak_end:
            # Peak hours
            return random.uniform(1.5, 2.0)
        elif merchant['type'] in ['transport', 'food_delivery']:
            # Extended service hours
            if 6 <= hour <= 23:
                return random.uniform(0.8, 1.2)
            else:
                return random.uniform(0.3, 0.6)
        else:
            # Regular business hours
            if 8 <= hour <= 20:
                return random.uniform(0.6, 1.0)
            else:
                return random.uniform(0.1, 0.3)

    def generate_seasonal_merchant_adjustments(self, merchant: Dict[str, Any], month: int) -> Dict[str, float]:
        """Generate seasonal adjustments for merchant activity."""
        seasonal_patterns = {
            'transport': {
                12: 1.3,  # December - holiday travel
                1: 0.8,   # January - post-holiday lull
                6: 1.2,   # June - summer travel
                7: 1.2,   # July - summer travel
                11: 1.1   # November - pre-holiday
            },
            'food_delivery': {
                12: 1.4,  # December - holiday orders
                1: 1.2,   # January - new year resolutions (healthy food)
                2: 1.3,   # February - Valentine's, CNY
                6: 0.9,   # June - people eat out more
                7: 0.9,   # July - vacation season
                11: 1.2   # November - Thanksgiving prep
            },
            'mart_grocery': {
                12: 1.5,  # December - holiday shopping
                1: 1.1,   # January - new year stock up
                3: 1.1,   # March - spring cleaning
                8: 1.2,   # August - back to school
                11: 1.3   # November - holiday prep
            },
            'financial_services': {
                1: 1.3,   # January - new year financial planning
                4: 1.2,   # April - tax season
                12: 1.1   # December - year-end planning
            }
        }
        
        base_multiplier = 1.0
        if merchant['type'] in seasonal_patterns:
            base_multiplier = seasonal_patterns[merchant['type']].get(month, 1.0)
        
        return {
            'volume_multiplier': base_multiplier,
            'avg_amount_multiplier': random(0.9, 1.1),
            'peak_hours_extension': 1 if month in [11, 12] else 0  # Extend hours during holidays
        }