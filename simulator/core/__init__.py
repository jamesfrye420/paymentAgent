"""
Core simulation components for the Realistic Payment Gateway Simulator.

This module contains the main simulator class and configuration management
for generating realistic payment data in the Grab ecosystem.
"""

from .simulator import RealisticPaymentSimulator
from .config import (
    SimulationConfig,
    GRAB_MERCHANT_TYPES,
    GRAB_TRANSACTION_AMOUNTS,
    GRAB_PEAK_HOURS,
    REGIONAL_DISTRIBUTION,
    COUNTRY_MAPPING,
    RISK_LEVEL_DISTRIBUTION,
    PAYMENT_METHOD_PREFERENCES,
    CARD_NETWORK_PREFERENCES,
    CARD_ISSUERS,
    WALLET_PREFERENCES,
    PRIMARY_CURRENCIES,
    LOCAL_CURRENCIES,
    FAILURE_SCENARIOS,
    FAILURE_PATTERNS
)

__version__ = "1.0.0"
__author__ = "Payment Gateway Simulation Team"

# Main exports
__all__ = [
    # Main simulator class
    "RealisticPaymentSimulator",
    
    # Configuration
    "SimulationConfig",
    
    # Grab ecosystem constants
    "GRAB_MERCHANT_TYPES",
    "GRAB_TRANSACTION_AMOUNTS", 
    "GRAB_PEAK_HOURS",
    
    # Regional and demographic data
    "REGIONAL_DISTRIBUTION",
    "COUNTRY_MAPPING",
    "RISK_LEVEL_DISTRIBUTION",
    
    # Payment preferences
    "PAYMENT_METHOD_PREFERENCES",
    "CARD_NETWORK_PREFERENCES",
    "CARD_ISSUERS",
    "WALLET_PREFERENCES",
    
    # Currency mapping
    "PRIMARY_CURRENCIES",
    "LOCAL_CURRENCIES",
    
    # Failure scenarios
    "FAILURE_SCENARIOS",
    "FAILURE_PATTERNS"
]

# Convenience functions for quick access
def create_simulator(customer_count: int = 1000, merchant_count: int = 50) -> RealisticPaymentSimulator:
    """
    Create a simulator with custom pool sizes.
    
    Args:
        customer_count: Number of customers to generate
        merchant_count: Number of merchants to generate
        
    Returns:
        Configured RealisticPaymentSimulator instance
    """
    config = SimulationConfig(
        customer_pool_size=customer_count,
        merchant_pool_size=merchant_count
    )
    return RealisticPaymentSimulator(config)


def create_stress_test_simulator() -> RealisticPaymentSimulator:
    """
    Create a simulator optimized for stress testing.
    
    Returns:
        RealisticPaymentSimulator configured for high-volume testing
    """
    config = SimulationConfig(
        customer_pool_size=2000,
        merchant_pool_size=100,
        failure_injection_probability=0.15,  # Higher failure rate
        base_delay=0.5,  # Faster processing
        stats_print_interval=25  # More frequent stats
    )
    return RealisticPaymentSimulator(config)


def create_grab_sea_simulator() -> RealisticPaymentSimulator:
    """
    Create a simulator optimized for Southeast Asian Grab ecosystem.
    
    Returns:
        RealisticPaymentSimulator with SEA-focused configuration
    """
    config = SimulationConfig(
        customer_pool_size=1500,
        merchant_pool_size=75,
        business_hours=(7, 22),  # Extended hours for SEA
        weekend_multiplier=0.8,  # Higher weekend activity in SEA
        failure_injection_probability=0.03  # Lower for mature market
    )
    return RealisticPaymentSimulator(config)


def create_development_simulator() -> RealisticPaymentSimulator:
    """
    Create a simulator optimized for development and testing.
    
    Returns:
        RealisticPaymentSimulator with development-friendly settings
    """
    config = SimulationConfig(
        customer_pool_size=100,  # Smaller pools for faster startup
        merchant_pool_size=20,
        base_delay=1.0,
        stats_print_interval=10,  # More frequent feedback
        failure_injection_probability=0.1  # More failures for testing
    )
    return RealisticPaymentSimulator(config)


# Module metadata
__doc__ = """
Realistic Payment Gateway Simulator - Core Module

This module provides the main simulation engine for generating realistic
payment transaction data based on the Grab ecosystem. It includes:

1. RealisticPaymentSimulator - Main simulation class
2. SimulationConfig - Configuration management
3. Regional and demographic constants
4. Payment method and network preferences
5. Grab-specific merchant types and patterns

Quick Start:
    from simulation.core import RealisticPaymentSimulator
    
    simulator = RealisticPaymentSimulator()
    simulator.run_simulation()

Advanced Usage:
    from simulation.core import create_grab_sea_simulator
    
    simulator = create_grab_sea_simulator()
    simulator.run_business_hours_simulation()

Configuration:
    from simulation.core import SimulationConfig, RealisticPaymentSimulator
    
    config = SimulationConfig(
        customer_pool_size=2000,
        failure_injection_probability=0.08
    )
    simulator = RealisticPaymentSimulator(config)
"""

# Version compatibility
def get_version() -> str:
    """Get the current version of the simulation core."""
    return __version__


def get_supported_regions() -> list:
    """Get list of supported regions."""
    return [region[0] for region in REGIONAL_DISTRIBUTION]


def get_grab_services() -> list:
    """Get list of Grab service types."""
    return [service[0] for service in GRAB_MERCHANT_TYPES]


def get_supported_networks() -> list:
    """Get list of supported card networks."""
    networks = set()
    for region_prefs in CARD_NETWORK_PREFERENCES.values():
        networks.update([network[0] for network in region_prefs])
    return list(networks)


def get_supported_payment_methods() -> list:
    """Get list of supported payment methods."""
    methods = set()
    for region_prefs in PAYMENT_METHOD_PREFERENCES.values():
        methods.update([method[0] for method in region_prefs])
    return list(methods)


# Validation functions
def validate_config(config: SimulationConfig) -> bool:
    """
    Validate simulation configuration.
    
    Args:
        config: SimulationConfig to validate
        
    Returns:
        True if configuration is valid
        
    Raises:
        ValueError: If configuration is invalid
    """
    if config.customer_pool_size <= 0:
        raise ValueError("Customer pool size must be positive")
    
    if config.merchant_pool_size <= 0:
        raise ValueError("Merchant pool size must be positive")
    
    if not (0.0 <= config.failure_injection_probability <= 1.0):
        raise ValueError("Failure injection probability must be between 0 and 1")
    
    if config.base_delay < 0:
        raise ValueError("Base delay must be non-negative")
    
    if config.min_delay < 0 or config.max_delay < config.min_delay:
        raise ValueError("Invalid delay configuration")
    
    if config.stats_print_interval <= 0:
        raise ValueError("Stats print interval must be positive")
    
    return True


# Export validation function
__all__.extend([
    "create_simulator",
    "create_stress_test_simulator", 
    "create_grab_sea_simulator",
    "create_development_simulator",
    "get_version",
    "get_supported_regions",
    "get_grab_services", 
    "get_supported_networks",
    "get_supported_payment_methods",
    "validate_config"
])