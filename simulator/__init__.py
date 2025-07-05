# simulation/__init__.py
"""
Realistic Payment Gateway Simulation Package

A comprehensive simulation system for generating realistic payment data
for training autonomous payment recovery agents.
"""

from .core.simulator import RealisticPaymentSimulator
from .main import main

__version__ = "1.0.0"
__author__ = "Payment Gateway Team"
__description__ = "Realistic Payment Gateway Simulation for LLM Training"

__all__ = [
    "RealisticPaymentSimulator",
    "main"
]


# simulation/core/__init__.py
"""Core simulation components."""

from core.simulator import RealisticPaymentSimulator
from core.config import SimulationConfig

__all__ = [
    "RealisticPaymentSimulator", 
    "SimulationConfig"
]


# simulation/data/__init__.py
"""Data generation components."""

from .data.customer_generator import CustomerGenerator
from .data.merchant_generator import MerchantGenerator
from .data.payment_generator import PaymentInstrumentGenerator

__all__ = [
    "CustomerGenerator",
    "MerchantGenerator", 
    "PaymentInstrumentGenerator"
]


# simulation/patterns/__init__.py
"""Pattern and behavior simulation components."""

# These will be available when pattern modules are created
# from .traffic_patterns import TrafficPatternManager
# from .failure_injection import FailureInjector
# from .business_patterns import BusinessPatternEngine

__all__ = [
    # "TrafficPatternManager",
    # "FailureInjector",
    # "BusinessPatternEngine"
]


# simulation/analysis/__init__.py
"""Analysis and reporting components."""

# These will be available when analysis modules are created
# from .stats_collector import StatsCollector
# from .pattern_analyzer import PaymentAnalyzer
# from .llm_training import LLMTrainingDataGenerator

__all__ = [
    # "StatsCollector",
    # "PaymentAnalyzer",
    # "LLMTrainingDataGenerator"
]


# simulation/utils/__init__.py
"""Utility components."""

from .utils.display import SimulationDisplay, ColorFormatter, TableFormatter, MetricsFormatter
from .utils.signal_handlers import setup_signal_handlers, GracefulShutdownHandler

__all__ = [
    "SimulationDisplay",
    "ColorFormatter", 
    "TableFormatter",
    "MetricsFormatter",
    "setup_signal_handlers",
    "GracefulShutdownHandler"
]