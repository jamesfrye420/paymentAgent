"""
Simulation configuration and constants.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class SimulationConfig:
    """Configuration for the payment simulation."""
    
    # Customer pool settings
    customer_pool_size: int = 1000
    merchant_pool_size: int = 50
    
    # Traffic patterns
    business_hours: Tuple[int, int] = (9, 17)  # 9 AM to 5 PM
    weekend_multiplier: float = 100.00  # 60% traffic on weekends
    
    # Failure injection
    failure_injection_probability: float = 1.0 
    failure_recovery_time_range: Tuple[float, float] = (10.0, 60.0)  # 10-60 seconds
    
    # Statistics
    stats_print_interval: int = 50  # Print stats every N transactions
    
    # Delays
    base_delay: float = 0.2  # Base seconds between payments
    min_delay: float = 0.1   # Minimum delay
    max_delay: float = 0.5  # Maximum delay


# Grab-specific merchant types based on their services
GRAB_MERCHANT_TYPES = [
    ('transport', 0.35),        # GrabCar, GrabBike, GrabTaxi, GrabShare
    ('food_delivery', 0.25),    # GrabFood restaurants and merchants
    ('mart_grocery', 0.15),     # GrabMart - groceries and essentials
    ('express_delivery', 0.10), # GrabExpress - courier and parcels
    ('financial_services', 0.08), # GrabPay, PayLater, GrabFin
    ('rewards_partners', 0.05), # GrabRewards partner merchants
    ('enterprise_b2b', 0.02)    # GrabForBusiness services
]

# Realistic transaction amounts by Grab service type
GRAB_TRANSACTION_AMOUNTS = {
    'transport': (8, 25),           # Typical ride fares
    'food_delivery': (12, 35),      # Meal orders
    'mart_grocery': (20, 80),       # Grocery shopping
    'express_delivery': (5, 20),    # Courier services
    'financial_services': (50, 500), # Loan payments, top-ups
    'rewards_partners': (15, 100),   # Partner merchant purchases
    'enterprise_b2b': (100, 2000)   # Corporate services
}

# Peak hours by Grab service type
GRAB_PEAK_HOURS = {
    'transport': (7, 9),          # Morning commute (+ evening 17-19)
    'food_delivery': (11, 14),    # Lunch (+ dinner 18-21)
    'mart_grocery': (17, 21),     # After work shopping
    'express_delivery': (9, 17),  # Business hours
    'financial_services': (10, 16), # Banking hours
    'rewards_partners': (12, 20),  # Shopping hours
    'enterprise_b2b': (9, 17)     # Business hours
}

# Regional distribution weights (realistic global distribution)
REGIONAL_DISTRIBUTION = [
    ('NORTH_AMERICA', 0.3),
    ('EUROPE', 0.25),
    ('SOUTHEAST_ASIA', 0.2),
    ('ASIA_PACIFIC', 0.15),
    ('LATIN_AMERICA', 0.1)
]

# Country mapping by region
COUNTRY_MAPPING = {
    'NORTH_AMERICA': ['US', 'CA', 'MX'],
    'EUROPE': ['GB', 'DE', 'FR', 'IT', 'ES'],
    'SOUTHEAST_ASIA': ['SG', 'MY', 'TH', 'ID', 'VN', 'PH'],
    'ASIA_PACIFIC': ['JP', 'KR', 'AU', 'NZ'],
    'LATIN_AMERICA': ['BR', 'AR', 'CL', 'CO']
}

# Risk level distribution (realistic)
RISK_LEVEL_DISTRIBUTION = [
    ('LOW', 0.7),
    ('MEDIUM', 0.25),
    ('HIGH', 0.05)
]

# Regional payment method preferences
PAYMENT_METHOD_PREFERENCES = {
    'NORTH_AMERICA': [
        ('CARD', 0.6),
        ('DIGITAL_WALLET', 0.3),
        ('BANK_TRANSFER', 0.1)
    ],
    'EUROPE': [
        ('CARD', 0.5),
        ('BANK_TRANSFER', 0.3),
        ('DIGITAL_WALLET', 0.2)
    ],
    'SOUTHEAST_ASIA': [
        ('DIGITAL_WALLET', 0.4),
        ('CARD', 0.35),
        ('BANK_TRANSFER', 0.25)
    ],
    'ASIA_PACIFIC': [
        ('CARD', 0.45),
        ('DIGITAL_WALLET', 0.35),
        ('BANK_TRANSFER', 0.2)
    ],
    'LATIN_AMERICA': [
        ('CARD', 0.4),
        ('BANK_TRANSFER', 0.35),
        ('DIGITAL_WALLET', 0.25)
    ]
}

# Regional card network preferences
CARD_NETWORK_PREFERENCES = {
    'NORTH_AMERICA': [
        ('VISA', 0.4),
        ('MASTERCARD', 0.35),
        ('AMEX', 0.15),
        ('DISCOVER', 0.1)
    ],
    'EUROPE': [
        ('VISA', 0.45),
        ('MASTERCARD', 0.45),
        ('AMEX', 0.08),
        ('DINERS', 0.02)
    ],
    'SOUTHEAST_ASIA': [
        ('VISA', 0.4),
        ('MASTERCARD', 0.35),
        ('UNIONPAY', 0.15),
        ('JCB', 0.1)
    ],
    'ASIA_PACIFIC': [
        ('VISA', 0.35),
        ('MASTERCARD', 0.3),
        ('JCB', 0.2),
        ('AMEX', 0.15)
    ]
}

# Realistic card issuers by country
CARD_ISSUERS = {
    'US': ['Chase Bank', 'Bank of America', 'Wells Fargo', 'Citi', 'Capital One'],
    'GB': ['Barclays', 'HSBC', 'Lloyds', 'NatWest', 'Santander'],
    'SG': ['DBS Bank', 'OCBC Bank', 'UOB', 'Standard Chartered', 'Maybank'],
    'DE': ['Deutsche Bank', 'Commerzbank', 'HypoVereinsbank', 'Postbank'],
    'JP': ['MUFG Bank', 'Sumitomo Mitsui', 'Mizuho Bank', 'Rakuten Bank'],
    'AU': ['Commonwealth Bank', 'Westpac', 'ANZ', 'NAB'],
    'CA': ['RBC', 'TD Bank', 'Scotiabank', 'BMO'],
    'FR': ['BNP Paribas', 'Crédit Agricole', 'Société Générale'],
    'MY': ['Maybank', 'CIMB Bank', 'Public Bank', 'RHB Bank'],
    'TH': ['Bangkok Bank', 'Kasikornbank', 'Siam Commercial Bank'],
    'ID': ['Bank Mandiri', 'BCA', 'BRI', 'BNI'],
    'VN': ['Vietcombank', 'BIDV', 'VietinBank', 'Techcombank'],
    'PH': ['BDO', 'BPI', 'Metrobank', 'UnionBank']
}

# Digital wallet preferences by region
WALLET_PREFERENCES = {
    'NORTH_AMERICA': ['apple_pay', 'google_pay', 'paypal', 'venmo'],
    'EUROPE': ['apple_pay', 'google_pay', 'paypal', 'klarna'],
    'SOUTHEAST_ASIA': ['grabpay', 'google_pay', 'apple_pay', 'touchngo'],
    'ASIA_PACIFIC': ['apple_pay', 'google_pay', 'alipay', 'wechat_pay'],
    'LATIN_AMERICA': ['mercado_pago', 'google_pay', 'apple_pay', 'pix']
}

# Primary currencies by region
PRIMARY_CURRENCIES = {
    'NORTH_AMERICA': 'USD',
    'EUROPE': 'EUR',
    'SOUTHEAST_ASIA': 'SGD',
    'ASIA_PACIFIC': 'USD',  # International transactions
    'LATIN_AMERICA': 'USD'
}

# Local currencies by country
LOCAL_CURRENCIES = {
    'GB': 'GBP',
    'SG': 'SGD',
    'MY': 'MYR',
    'TH': 'THB',
    'ID': 'IDR',
    'VN': 'VND',
    'PH': 'PHP'
}

# Available failure scenarios
FAILURE_SCENARIOS = [
    'stripe_maintenance',
    'adyen_high_latency',
    'paypal_low_success',
    'razorpay_rate_limit'
]

FAILURE_PATTERNS = {
    'peak_hour_stress': {
        'probability': 0.25,  # 25% during peak hours
        'scenarios': ['adyen_high_latency', 'stripe_maintenance', 'provider_overload']
    },
    'weekend_issues': {
        'probability': 0.12,  # 12% on weekends
        'scenarios': ['paypal_low_success', 'network_partition']
    },
    'high_value_scrutiny': {
        'probability': 0.30,  # 30% for transactions > $1000
        'scenarios': ['circuit_breaker_test', 'database_timeout']
    },
    'regional_problems': {
        'probability': 0.20,  # 20% for certain regions
        'scenarios': ['razorpay_rate_limit', 'mass_failure']
    },
    'night_maintenance': {
        'probability': 0.18,  # 18% during 2-6 AM
        'scenarios': ['stripe_maintenance', 'database_timeout', 'provider_overload']
    },
    'fraud_detection_spike': {
        'probability': 0.35,  # 35% for high-risk customers
        'scenarios': ['circuit_breaker_test', 'paypal_low_success']
    },
    'mobile_network_issues': {
        'probability': 0.22,  # 22% for mobile wallet payments
        'scenarios': ['network_partition', 'adyen_high_latency']
    },
    'cross_border_complications': {
        'probability': 0.28,  # 28% for international transactions
        'scenarios': ['razorpay_rate_limit', 'mass_failure', 'database_timeout']
    }
}