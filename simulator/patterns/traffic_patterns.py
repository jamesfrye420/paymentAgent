"""
Traffic pattern management for realistic payment simulation.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from ..core.config import SimulationConfig


class TrafficPatternManager:
    """Manages realistic traffic patterns based on time, merchant type, and region."""
    
    def __init__(self, config: SimulationConfig = None):
        """Initialize traffic pattern manager."""
        self.config = config or SimulationConfig()
        self.base_delay = self.config.base_delay
        self.min_delay = self.config.min_delay
        self.max_delay = self.config.max_delay
        
        # Traffic multipliers by hour (24-hour format)
        self.hourly_multipliers = self._generate_hourly_patterns()
        
        # Day of week multipliers (0=Monday, 6=Sunday)
        self.daily_multipliers = {
            0: 1.0,   # Monday
            1: 1.1,   # Tuesday - slight increase
            2: 1.15,  # Wednesday - peak weekday
            3: 1.1,   # Thursday
            4: 1.2,   # Friday - highest weekday
            5: 0.8,   # Saturday - weekend reduction
            6: 0.6    # Sunday - lowest traffic
        }
        
        # Seasonal multipliers by month
        self.seasonal_multipliers = {
            1: 0.85,  # January - post-holiday lull
            2: 0.9,   # February
            3: 1.0,   # March - baseline
            4: 1.05,  # April - spring activity
            5: 1.1,   # May
            6: 1.15,  # June - summer peak
            7: 1.2,   # July - summer peak
            8: 1.1,   # August
            9: 1.05,  # September - back to school/work
            10: 1.0,  # October
            11: 1.25, # November - pre-holiday surge
            12: 1.4   # December - holiday peak
        }
    
    def _generate_hourly_patterns(self) -> Dict[int, float]:
        """Generate realistic hourly traffic patterns."""
        # Base pattern for general e-commerce/payment traffic
        patterns = {
            0: 0.1,   # Midnight - very low
            1: 0.05,  # 1 AM - lowest
            2: 0.05,  # 2 AM - lowest
            3: 0.05,  # 3 AM - lowest
            4: 0.1,   # 4 AM - very low
            5: 0.2,   # 5 AM - early commuters
            6: 0.4,   # 6 AM - morning commute starts
            7: 0.8,   # 7 AM - commute peak
            8: 1.2,   # 8 AM - business hours start
            9: 1.5,   # 9 AM - morning business peak
            10: 1.3,  # 10 AM - morning activity
            11: 1.4,  # 11 AM - pre-lunch
            12: 1.8,  # Noon - lunch peak
            13: 1.6,  # 1 PM - lunch continues
            14: 1.2,  # 2 PM - afternoon lull
            15: 1.3,  # 3 PM - afternoon pickup
            16: 1.4,  # 4 PM - late afternoon
            17: 1.6,  # 5 PM - end of work day
            18: 1.8,  # 6 PM - evening commute
            19: 2.0,  # 7 PM - evening peak (dinner, shopping)
            20: 1.8,  # 8 PM - evening activity
            21: 1.5,  # 9 PM - evening wind down
            22: 1.0,  # 10 PM - night activity
            23: 0.5   # 11 PM - late night
        }
        return patterns
    
    def get_traffic_multiplier(self, timestamp: datetime = None) -> float:
        """Calculate traffic multiplier based on current time patterns."""
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        month = timestamp.month
        
        # Base hourly multiplier
        hourly_mult = self.hourly_multipliers.get(hour, 1.0)
        
        # Day of week adjustment
        daily_mult = self.daily_multipliers.get(day_of_week, 1.0)
        
        # Seasonal adjustment
        seasonal_mult = self.seasonal_multipliers.get(month, 1.0)
        
        # Combine all multipliers
        total_multiplier = hourly_mult * daily_mult * seasonal_mult
        
        # Add some randomness (±20%)
        variance = random.uniform(0.8, 1.2)
        
        return total_multiplier * variance
    
    def get_merchant_specific_multiplier(self, merchant: Dict[str, Any], 
                                       timestamp: datetime = None) -> float:
        """Get traffic multiplier specific to merchant type and timing."""
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour
        merchant_type = merchant.get('type', 'transport')
        
        # Merchant-specific patterns
        merchant_patterns = self._get_merchant_hourly_patterns(merchant_type)
        
        # Base multiplier for this merchant type at this hour
        base_mult = merchant_patterns.get(hour, 1.0)
        
        # Check if within merchant's peak hours
        peak_start, peak_end = merchant.get('peak_hours', (9, 17))
        if peak_start <= hour <= peak_end:
            peak_mult = random.uniform(1.8, 2.5)  # Strong peak boost
        elif self._is_extended_hours(merchant_type, hour):
            peak_mult = random.uniform(1.2, 1.6)  # Moderate extended hours
        else:
            peak_mult = random.uniform(0.3, 0.7)  # Off hours reduction

        return base_mult * peak_mult
    
    def _get_merchant_hourly_patterns(self, merchant_type: str) -> Dict[int, float]:
        """Get hourly patterns specific to merchant types."""
        patterns = {
            'transport': {
                # Two peaks: morning commute and evening commute
                6: 1.5, 7: 2.0, 8: 2.5, 9: 1.8,
                17: 1.8, 18: 2.5, 19: 2.0, 20: 1.5,
                # Weekend late night rides
                22: 1.2, 23: 1.0, 0: 0.8, 1: 0.6
            },
            'food_delivery': {
                # Three peaks: breakfast, lunch, dinner
                7: 1.2, 8: 1.5, 9: 1.3,  # Breakfast
                11: 1.8, 12: 2.5, 13: 2.2, 14: 1.6,  # Lunch
                18: 2.0, 19: 2.8, 20: 2.5, 21: 2.0, 22: 1.5  # Dinner
            },
            'mart_grocery': {
                # Evening shopping after work, weekend mornings
                10: 1.3, 11: 1.2,  # Weekend mornings
                17: 1.5, 18: 2.0, 19: 2.2, 20: 1.8, 21: 1.4  # Evening shopping
            },
            'express_delivery': {
                # Business hours focused
                9: 1.5, 10: 1.8, 11: 2.0, 12: 1.6,
                13: 1.4, 14: 1.8, 15: 2.0, 16: 1.8, 17: 1.5
            },
            'financial_services': {
                # Banking hours with lunch dip
                9: 1.8, 10: 2.0, 11: 1.9, 12: 1.2,
                13: 1.3, 14: 1.8, 15: 2.0, 16: 1.6
            },
            'rewards_partners': {
                # Shopping hours - evenings and weekends
                12: 1.4, 13: 1.3,  # Lunch shopping
                17: 1.6, 18: 1.8, 19: 2.0, 20: 1.9, 21: 1.5  # Evening shopping
            },
            'enterprise_b2b': {
                # Strict business hours
                9: 1.5, 10: 2.0, 11: 1.8, 14: 1.8, 15: 2.0, 16: 1.5
            }
        }
        
        return patterns.get(merchant_type, {})
    
    def _is_extended_hours(self, merchant_type: str, hour: int) -> bool:
        """Check if merchant type operates during extended hours."""
        extended_hour_services = {
            'transport': (5, 24),      # 5 AM to midnight
            'food_delivery': (6, 23),  # 6 AM to 11 PM
            'mart_grocery': (7, 22),   # 7 AM to 10 PM
        }
        
        if merchant_type in extended_hour_services:
            start, end = extended_hour_services[merchant_type]
            return start <= hour <= end
        
        return False
    
    def calculate_payment_delay(self, timestamp: datetime = None, 
                              merchant: Dict[str, Any] = None) -> float:
        """Calculate realistic delay between payments."""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Get overall traffic multiplier
        traffic_mult = self.get_traffic_multiplier(timestamp)
        
        # Get merchant-specific multiplier if provided
        if merchant:
            merchant_mult = self.get_merchant_specific_multiplier(merchant, timestamp)
            traffic_mult *= merchant_mult
        
        # Higher traffic = shorter delays between payments
        delay = self.base_delay / max(traffic_mult, 0.1)
        
        # Add realistic variance
        delay *= random.uniform(0.5, 2.0)

        # Ensure within bounds
        return max(self.min_delay, min(delay, self.max_delay))
    
    def get_expected_volume(self, duration_hours: float, 
                          merchant_type: str = None,
                          timestamp: datetime = None) -> int:
        """Estimate expected payment volume for a time period."""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Base payments per hour (calibrated from real data)
        base_volume_per_hour = {
            'transport': 50,         # High frequency, low value
            'food_delivery': 30,     # Medium frequency
            'mart_grocery': 20,      # Lower frequency, higher value
            'express_delivery': 25,  # Medium frequency
            'financial_services': 15, # Low frequency, high value
            'rewards_partners': 10,   # Low frequency
            'enterprise_b2b': 5      # Very low frequency, very high value
        }
        
        base_hourly = base_volume_per_hour.get(merchant_type, 25)
        
        # Apply traffic multipliers
        total_volume = 0
        current_time = timestamp
        
        for hour in range(int(duration_hours)):
            traffic_mult = self.get_traffic_multiplier(current_time)
            hourly_volume = base_hourly * traffic_mult
            total_volume += hourly_volume
            current_time += timedelta(hours=1)
        
        # Handle partial hour
        if duration_hours % 1 > 0:
            partial_hour = duration_hours % 1
            traffic_mult = self.get_traffic_multiplier(current_time)
            total_volume += base_hourly * traffic_mult * partial_hour
        
        return int(total_volume)
    
    def get_rush_hour_info(self, timestamp: datetime = None) -> Dict[str, Any]:
        """Get information about current rush hour status."""
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        
        # Define rush hours
        morning_rush = (7, 9)
        lunch_rush = (12, 14)
        evening_rush = (17, 20)
        
        rush_info = {
            'is_rush_hour': False,
            'rush_type': None,
            'intensity': 0.0,
            'multiplier': 1.0
        }
        
        if morning_rush[0] <= hour <= morning_rush[1]:
            rush_info.update({
                'is_rush_hour': True,
                'rush_type': 'morning_commute',
                'intensity': 0.8 if day_of_week < 5 else 0.4,  # Weekday vs weekend
                'multiplier': 2.0 if day_of_week < 5 else 1.2
            })
        elif lunch_rush[0] <= hour <= lunch_rush[1]:
            rush_info.update({
                'is_rush_hour': True,
                'rush_type': 'lunch_hour',
                'intensity': 0.9,
                'multiplier': 2.2
            })
        elif evening_rush[0] <= hour <= evening_rush[1]:
            rush_info.update({
                'is_rush_hour': True,
                'rush_type': 'evening_commute',
                'intensity': 0.9 if day_of_week < 5 else 0.6,
                'multiplier': 2.3 if day_of_week < 5 else 1.4
            })
        
        return rush_info
    
    def simulate_traffic_surge(self, base_multiplier: float = 1.0, 
                             surge_factor: float = 3.0,
                             duration_minutes: int = 30) -> Dict[str, Any]:
        """Simulate sudden traffic surge (like during events or emergencies)."""
        surge_info = {
            'is_surge': True,
            'surge_factor': surge_factor,
            'base_multiplier': base_multiplier,
            'effective_multiplier': base_multiplier * surge_factor,
            'duration_minutes': duration_minutes,
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(minutes=duration_minutes),
            'reason': random.choice([
                'Major event ending',
                'Weather emergency',
                'Public transport disruption',
                'Promotional campaign',
                'Holiday rush',
                'System recovery after outage'
            ])
        }
        
        return surge_info
    
    def get_regional_traffic_adjustment(self, region: str, 
                                      timestamp: datetime = None) -> float:
        """Get traffic adjustment based on regional patterns."""
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour
        
        # Regional patterns based on business culture and time zones
        regional_adjustments = {
            'NORTH_AMERICA': {
                # Early start, late finish
                6: 1.2, 7: 1.5, 8: 1.3, 22: 1.2, 23: 1.0
            },
            'EUROPE': {
                # Lunch break culture
                12: 0.8, 13: 0.6, 14: 0.8, 15: 1.2
            },
            'SOUTHEAST_ASIA': {
                # Later start, extended evening
                10: 1.3, 11: 1.4, 20: 1.5, 21: 1.4, 22: 1.2
            },
            'ASIA_PACIFIC': {
                # Business-focused hours
                9: 1.4, 10: 1.5, 16: 1.3, 17: 1.4
            },
            'LATIN_AMERICA': {
                # Siesta culture
                13: 0.7, 14: 0.5, 15: 0.7, 16: 1.2
            }
        }
        
        adjustments = regional_adjustments.get(region, {})
        return adjustments.get(hour, 1.0)