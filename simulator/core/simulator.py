"""
Core payment gateway simulator for realistic transaction generation.
"""

import sys
import os
import time
import random
import threading
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from unittest import result
import uuid

# Add faker for realistic data generation
try:
    from faker import Faker
    from faker.providers import credit_card, company, internet, phone_number
except ImportError:
    print("Installing faker library...")
    os.system("pip install faker")
    from faker import Faker
    from faker.providers import credit_card, company, internet, phone_number

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from payment_gateway.gateway.payment_gateway import PaymentGateway
from payment_gateway.core.enums import (
    RoutingStrategy,
    RiskLevel,
    TransactionType,
)
from payment_gateway.core.models import (
    PaymentInstrument,
    CustomerInfo,
    Transaction as TransactionModel,
)

# Try relative imports first (when run as module)
from data.customer_generator import CustomerGenerator
from data.merchant_generator import MerchantGenerator
from data.payment_generator import PaymentInstrumentGenerator
from utils.display import SimulationDisplay, MetricsFormatter
from .config import SimulationConfig, FAILURE_SCENARIOS, FAILURE_PATTERNS


class RealisticPaymentSimulator:
    """
    Comprehensive payment gateway simulator with realistic data patterns.

    Generates realistic payment traffic based on Grab's ecosystem with:
    - Regional customer preferences
    - Grab service types (transport, food, mart, etc.)
    - Time-based traffic patterns
    - Dynamic failure injection
    - Comprehensive logging for LLM training
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        """Initialize the simulator with realistic data generators."""
        self.config = config or SimulationConfig()

        # Initialize Faker
        self.fake = Faker()
        self.fake.add_provider(credit_card)
        self.fake.add_provider(company)
        self.fake.add_provider(internet)
        self.fake.add_provider(phone_number)

        # Initialize data generators
        self.customer_generator = CustomerGenerator()
        self.merchant_generator = MerchantGenerator()
        self.payment_generator = PaymentInstrumentGenerator()

        # Initialize gateway and logger
        self.gateway = PaymentGateway(routing_strategy=RoutingStrategy.COST_OPTIMIZED)

        # Simulation control
        self.running = False
        self._log_filename = f"realistic_payment_result_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.stats = {
            "total_payments": 0,
            "successful_payments": 0,
            "failed_payments": 0,
            "by_network": {},
            "by_method": {},
            "by_region": {},
            "by_merchant_type": {},
            "by_amount_range": {},
            "scenarios_triggered": [],
        }

        self._events: List[Dict[str, Any]] = []

        # Configuration from config
        self.business_hours = self.config.business_hours
        self.weekend_multiplier = self.config.weekend_multiplier
        self.failure_injection_probability = self.config.failure_injection_probability

        # Generate customer and merchant pools
        self.customer_pool = self.customer_generator.generate_customer_pool(
            self.config.customer_pool_size
        )
        self.merchant_pool = self.merchant_generator.generate_merchant_pool(
            self.config.merchant_pool_size
        )

        SimulationDisplay.print_simulation_startup(
            len(self.customer_pool), len(self.merchant_pool)
        )

    def process_single_payment(self):
        """Process a single realistic payment transaction."""
        try:
            # Select random customer and merchant
            customer = random.choice(self.customer_pool)
            merchant = random.choice(self.merchant_pool)

            # Generate realistic payment context
            payment_instrument = (
                self.payment_generator.generate_payment_for_merchant_type(
                    customer, merchant["type"]
                )
            )
            amount = self._calculate_realistic_amount(customer, merchant)
            currency = self.payment_generator.generate_currency_for_transaction(
                customer, merchant
            )

            # Generate order ID and other metadata
            order_id = f"ord_{merchant['type']}_{self.fake.uuid4()[:12]}"

            # Occasionally inject failures based on context
            if self._should_inject_failure():
                self._inject_contextual_failure(amount, customer.region.value)

            # Process payment
            result = self.gateway.process_payment(
                amount=amount,
                currency=currency,
                payment_instrument=payment_instrument,
                customer_info=customer,
                merchant_id=merchant["merchant_id"],
                order_id=order_id,
                transaction_type=TransactionType.PAYMENT,
            )
            # Update statistics
            self._update_stats(result, customer, merchant, payment_instrument)

            # Print transaction summary
            SimulationDisplay.print_transaction(
                result, payment_instrument, customer, merchant, order_id
            )

            # Log structured event for LLM training
            self._log_payment_event(
                result, payment_instrument, customer, merchant, order_id
            )

        except Exception as e:
            print(f"❌ Payment processing error: {str(e)}")
            self.stats["failed_payments"] += 1
            self.stats["total_payments"] += 1

    def _calculate_realistic_amount(
        self, customer: CustomerInfo, merchant: Dict[str, Any]
    ) -> float:
        """Calculate realistic transaction amounts based on context."""
        base_amount = merchant["avg_transaction_value"]

        # Customer behavior patterns
        if customer.risk_level == RiskLevel.HIGH:
            # High-risk customers tend to have unusual amounts
            base_amount *= random.choice([0.1, 0.2, 5.0, 10.0])
        elif customer.successful_payments > 100:
            # Loyal customers tend to spend more
            base_amount *= random.uniform(1.2, 2.5)

        # Time-based patterns
        hour = datetime.now().hour
        peak_start, peak_end = merchant["peak_hours"]
        if peak_start <= hour <= peak_end:
            base_amount *= random.uniform(1.1, 1.4)  # Higher amounts during peak

        # Merchant type specific adjustments
        if merchant["type"] == "financial_services":
            # Financial services have wider range
            base_amount *= random.uniform(0.5, 5.0)
        elif merchant["type"] == "enterprise_b2b":
            # B2B transactions are typically larger
            base_amount *= random.uniform(2.0, 10.0)

        # Add realistic variance
        variance = random.uniform(0.7, 1.8)
        amount = base_amount * variance

        # Round to realistic values based on amount
        if amount < 10:
            return round(amount, 2)
        elif amount < 100:
            return round(amount / 5) * 5  # Round to nearest $5
        else:
            return round(amount / 10) * 10  # Round to nearest $10

    def _calculate_risk_score(
        self,
        customer: CustomerInfo,
        transaction_amount: float,
        payment_instrument: PaymentInstrument,
        merchant: Dict[str, Any],
    ) -> float:
        """Calculate comprehensive risk score for transaction."""
        risk_score = 0.0

        # Base customer risk (0-30 points)
        customer_risk_mapping = {"LOW": 5, "MEDIUM": 15, "HIGH": 30}
        risk_score += customer_risk_mapping.get(customer.risk_level.name, 15)

        # Transaction amount risk (0-25 points)
        if transaction_amount > 1000:
            risk_score += 25
        elif transaction_amount > 500:
            risk_score += 15
        elif transaction_amount > 100:
            risk_score += 5

        # Payment method risk (0-20 points)
        method_risk = {
            "CARD": 5,
            "DIGITAL_WALLET": 3,
            "BANK_TRANSFER": 2,
            "BUY_NOW_PAY_LATER": 15,
        }
        risk_score += method_risk.get(payment_instrument.method.name, 10)

        # Customer history risk (0-15 points)
        if customer.previous_failures > 5:
            risk_score += 15
        elif customer.previous_failures > 2:
            risk_score += 8

        if customer.successful_payments < 5:
            risk_score += 10  # New customer
        elif customer.successful_payments > 100:
            risk_score -= 5  # Loyal customer bonus

        # Geographic risk (0-10 points)
        high_risk_countries = ["NG", "GH", "KE", "BD"]  # Example high-risk countries
        if customer.country in high_risk_countries:
            risk_score += 10

        # Card-specific risks (0-15 points)
        if payment_instrument.method.name == "CARD":
            # International card for domestic transaction
            if payment_instrument.country_code != customer.country:
                risk_score += 8

            # High-risk card networks
            high_risk_networks = ["UNIONPAY", "DINERS"]
            if (
                payment_instrument.network
                and payment_instrument.network.name in high_risk_networks
            ):
                risk_score += 5

            # Expired card check
            current_year = datetime.now().year
            current_month = datetime.now().month
            if (
                payment_instrument.expiry_year
                and payment_instrument.expiry_month
                and (
                    payment_instrument.expiry_year < current_year
                    or (
                        payment_instrument.expiry_year == current_year
                        and payment_instrument.expiry_month < current_month
                    )
                )
            ):
                risk_score += 15

        # Merchant category risk (0-10 points)
        high_risk_merchants = ["financial_services", "enterprise_b2b"]
        if merchant["type"] in high_risk_merchants:
            risk_score += 5

        # Time-based risk (0-5 points)
        hour = datetime.now().hour
        if hour < 6 or hour > 23:  # Late night/early morning transactions
            risk_score += 5

        # Normalize to 0-100 scale
        risk_score = min(100, max(0, risk_score))

        return round(risk_score, 1)

    def _should_inject_failure(self) -> bool:
        """Decide whether to inject a failure scenario based on context."""
        base_probability = self.failure_injection_probability

        # Get current context
        hour = datetime.now().hour
        is_weekend = datetime.now().weekday() >= 5

        # Check enhanced failure patterns
        enhanced_probability = base_probability

        # Peak hour stress (7-9 AM, 12-2 PM, 5-7 PM)
        if (7 <= hour <= 9) or (12 <= hour <= 14) or (17 <= hour <= 19):
            pattern = FAILURE_PATTERNS.get("peak_hour_stress", {})
            enhanced_probability = max(
                enhanced_probability, pattern.get("probability", base_probability)
            )

        # Weekend issues
        if is_weekend:
            pattern = FAILURE_PATTERNS.get("weekend_issues", {})
            enhanced_probability = max(
                enhanced_probability, pattern.get("probability", base_probability)
            )

        return random.random() < enhanced_probability

    def _inject_contextual_failure(
        self, transaction_amount: float = 0, customer_region: str = ""
    ):
        """Inject failure scenarios based on transaction context."""
        hour = datetime.now().hour
        is_weekend = datetime.now().weekday() >= 5

        # Select appropriate failure pattern
        if transaction_amount > 1000:
            # High-value transaction failures
            pattern = FAILURE_PATTERNS.get("high_value_scrutiny", {})
            scenarios = pattern.get("scenarios", FAILURE_SCENARIOS)
            probability = pattern.get("probability", 0.3)
        elif customer_region in ["SOUTHEAST_ASIA", "ASIA_PACIFIC"]:
            # Regional issues
            pattern = FAILURE_PATTERNS.get("regional_problems", {})
            scenarios = pattern.get("scenarios", FAILURE_SCENARIOS)
            probability = pattern.get("probability", 0.2)
        elif (7 <= hour <= 9) or (12 <= hour <= 14) or (17 <= hour <= 19):
            # Peak hour stress
            pattern = FAILURE_PATTERNS.get("peak_hour_stress", {})
            scenarios = pattern.get("scenarios", FAILURE_SCENARIOS)
            probability = pattern.get("probability", 0.25)
        elif is_weekend:
            # Weekend issues
            pattern = FAILURE_PATTERNS.get("weekend_issues", {})
            scenarios = pattern.get("scenarios", FAILURE_SCENARIOS)
            probability = pattern.get("probability", 0.12)
        else:
            # Default failures
            scenarios = FAILURE_SCENARIOS
            probability = self.failure_injection_probability

        if random.random() < probability:
            scenario = random.choice(scenarios)
            result = self.gateway.simulate_scenario(scenario)

            if result["success"]:
                self.stats["scenarios_triggered"].append(
                    {
                        "scenario": scenario,
                        "timestamp": datetime.now().isoformat(),
                        "message": result["message"],
                        "context": {
                            "transaction_amount": transaction_amount,
                            "customer_region": customer_region,
                            "hour": hour,
                            "is_weekend": is_weekend,
                            "pattern_used": "contextual_injection",
                        },
                    }
                )
                SimulationDisplay.print_scenario_injection(scenario, result["message"])

                # Schedule recovery after random time
                recovery_time = random.uniform(*self.config.failure_recovery_time_range)
                threading.Timer(recovery_time, self._recover_from_failure).start()

    def _inject_random_failure(self):
        """Randomly inject failure scenarios to simulate real-world issues."""
        scenario = random.choice(FAILURE_SCENARIOS)
        result = self.gateway.simulate_scenario(scenario)

        if result["success"]:
            self.stats["scenarios_triggered"].append(
                {
                    "scenario": scenario,
                    "timestamp": datetime.now().isoformat(),
                    "message": result["message"],
                }
            )
            SimulationDisplay.print_scenario_injection(scenario, result["message"])

            # Schedule recovery after random time
            recovery_time = random.uniform(*self.config.failure_recovery_time_range)
            threading.Timer(recovery_time, self._recover_from_failure).start()

    def _recover_from_failure(self):
        """Recover from injected failure scenarios."""
        result = self.gateway.simulate_scenario("reset_all")
        if result["success"]:
            SimulationDisplay.print_scenario_recovery()

    def _generate_fraud_indicators(
        self,
        risk_score: float,
        customer: CustomerInfo,
        payment_instrument: PaymentInstrument,
    ) -> List[str]:
        """Generate fraud indicators based on risk factors."""
        indicators = []

        if risk_score > 70:
            indicators.append("HIGH_RISK_SCORE")

        if customer.previous_failures > 3:
            indicators.append("MULTIPLE_RECENT_FAILURES")

        if payment_instrument.method.name == "CARD":
            # Check for expired card
            current_year = datetime.now().year
            current_month = datetime.now().month
            if (
                payment_instrument.expiry_year
                and payment_instrument.expiry_month
                and (
                    payment_instrument.expiry_year < current_year
                    or (
                        payment_instrument.expiry_year == current_year
                        and payment_instrument.expiry_month < current_month
                    )
                )
            ):
                indicators.append("EXPIRED_CARD")

            # International card
            if payment_instrument.country_code != customer.country:
                indicators.append("INTERNATIONAL_CARD")

        if customer.successful_payments < 3:
            indicators.append("NEW_CUSTOMER")

        # Velocity check (simulated)
        if random.random() < 0.1:  # 10% chance of velocity flag
            indicators.append("HIGH_VELOCITY")

        return indicators

    def _calculate_traffic_multiplier(self) -> float:
        """Calculate traffic multiplier based on time patterns."""
        now = datetime.now()
        hour = now.hour
        is_weekend = now.weekday() >= 5

        # Base multiplier
        multiplier = 1.0

        # Business hours effect
        if self.business_hours[0] <= hour <= self.business_hours[1]:
            multiplier *= 2.0  # Double traffic during business hours
        elif 18 <= hour <= 23:
            multiplier *= 1.5  # Increased evening traffic
        else:
            multiplier *= 0.5  # Reduced off-hours traffic

        # Weekend effect
        if is_weekend:
            multiplier *= self.weekend_multiplier

        # Grab-specific patterns
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            # Transport peak hours
            multiplier *= 1.3
        elif 11 <= hour <= 14 or 18 <= hour <= 21:
            # Food delivery peak hours
            multiplier *= 1.2

        # Add some randomness
        multiplier *= random.uniform(0.8, 1.2)

        return multiplier

    def _calculate_delay(self) -> float:
        """Calculate realistic delay between payments."""
        traffic_multiplier = self._calculate_traffic_multiplier()

        # Base delay (seconds between payments)
        base_delay = self.config.base_delay

        # Adjust based on traffic (higher traffic = shorter delays)
        delay = base_delay / traffic_multiplier

        # Add realistic variance
        delay *= random.uniform(0.5, 2.0)

        # Ensure minimum and maximum delays
        return max(self.config.min_delay, min(delay, self.config.max_delay))

    def _update_stats(
        self,
        transaction_result: Dict[str, Any],
        customer: CustomerInfo,
        merchant: Dict[str, Any],
        payment_instrument: PaymentInstrument,
    ):
        """Update simulation statistics."""
        self.stats["total_payments"] += 1

        if transaction_result["success"]:
            self.stats["successful_payments"] += 1
        else:
            self.stats["failed_payments"] += 1

        # Track by network
        if payment_instrument.network:
            network = payment_instrument.network.value
            self.stats["by_network"][network] = (
                self.stats["by_network"].get(network, 0) + 1
            )

        # Track by method
        method = payment_instrument.method.value
        self.stats["by_method"][method] = self.stats["by_method"].get(method, 0) + 1

        # Track by region
        region = customer.region.value
        self.stats["by_region"][region] = self.stats["by_region"].get(region, 0) + 1

        # Track by merchant type
        merchant_type = merchant["type"]
        self.stats["by_merchant_type"][merchant_type] = (
            self.stats["by_merchant_type"].get(merchant_type, 0) + 1
        )

        # Track by amount range
        amount = transaction_result["transaction"]["amount"]
        if amount < 25:
            range_key = "0-25"
        elif amount < 100:
            range_key = "25-100"
        elif amount < 500:
            range_key = "100-500"
        else:
            range_key = "500+"

        self.stats["by_amount_range"][range_key] = (
            self.stats["by_amount_range"].get(range_key, 0) + 1
        )

    # def _log_payment_event(self, result: Dict[str, Any], payment_instrument: PaymentInstrument,
    #                       customer: CustomerInfo, merchant: Dict[str, Any], order_id: str):
    #     """Log structured event for LLM training."""
    #     print(payment_instrument)
    #     if not self.logger:
    #         return

    #     try:
    #         transaction_data = result['transaction']

    #         # Create transaction model for logging
    #         transaction_obj = TransactionModel(
    #             id=transaction_data['id'],
    #             amount=transaction_data['amount'],
    #             currency=Currency(transaction_data['currency']),
    #             transaction_type=TransactionType.PAYMENT,
    #             provider=transaction_data['provider'],
    #             status=transaction_data['status'],
    #             payment_instrument=payment_instrument,
    #             customer_info=customer,
    #             merchant_id=merchant['merchant_id'],
    #             order_id=order_id
    #         )

    #         from payment_gateway.core.models import PaymentEvent
    #         event = PaymentEvent(
    #             event_type="realistic_payment_simulation",
    #             transaction=transaction_obj,
    #             provider=transaction_data['provider'],
    #             metadata={
    #                 'merchant_type': merchant['type'],
    #                 'merchant_name': merchant['name'],
    #                 'merchant_country': merchant['country'],
    #                 'merchant_volume_tier': merchant.get('volume_tier', 'medium'),
    #                 'commission_rate': merchant.get('commission_rate', 0.15),
    #                 'business_model': merchant.get('business_model', 'commission_based'),
    #                 'simulation_context': 'realistic_traffic',
    #                 'time_of_day': datetime.now().hour,
    #                 'day_of_week': datetime.now().weekday(),
    #                 'is_peak_hour': self._is_peak_hour(merchant),
    #                 'traffic_multiplier': self._calculate_traffic_multiplier()
    #             }
    #         )

    #         self.logger.log_payment_event(event)

    #         # Log routing decision if available
    #         if transaction_data.get('route_history'):
    #             latest_route = transaction_data['route_history'][-1]
    #             routing_decision = latest_route.get('routing_decision')
    #             if routing_decision:
    #                 self.logger.log_routing_decision(
    #                     transaction=transaction_obj,
    #                     decision_factors=routing_decision.get('decision_factors', {}),
    #                     selected_provider=transaction_data['provider'],
    #                     alternatives=routing_decision.get('alternative_providers', [])
    #                 )

    #     except Exception as e:
    #         # Don't let logging errors break the simulation
    #         pass

    # def _log_payment_event(self, result: Dict[str, Any], payment_instrument: PaymentInstrument,
    #                   customer: CustomerInfo, merchant: Dict[str, Any], order_id: str):
    #     """Log structured event for LLM training with risk scoring."""
    #     if not self.logger:
    #         return

    #     print('result',result)
    #     # print('payment_instrument',payment_instrument)
    #     # print('customer',customer)
    #     # print('merchant',merchant)

    #     try:
    #         with open(self._log_filename, "a") as f:
    #             f.write(json.dumps(result, default=str) + "\n")
    #     except Exception as e:
    #         SimulationDisplay.print_export_error(str(e))

    # try:
    #     transaction_data = result['transaction']

    #     # Calculate risk score and fraud indicators
    #     risk_score = self._calculate_risk_score(customer, transaction_data['amount'], payment_instrument, merchant)
    #     fraud_indicators = self._generate_fraud_indicators(risk_score, customer, payment_instrument)

    #     # Update transaction with risk data
    #     transaction_data['risk_score'] = risk_score
    #     transaction_data['fraud_indicators'] = fraud_indicators

    #     # Create transaction model for logging
    #     transaction_obj = TransactionModel(
    #         id=transaction_data['id'],
    #         amount=transaction_data['amount'],
    #         currency=Currency(transaction_data['currency']),
    #         transaction_type=TransactionType.PAYMENT,
    #         provider=transaction_data['provider'],
    #         status=transaction_data['status'],
    #         payment_instrument=payment_instrument,
    #         customer_info=customer,
    #         merchant_id=merchant['merchant_id'],
    #         order_id=order_id
    #     )

    #     from payment_gateway.core.models import PaymentEvent
    #     event = PaymentEvent(
    #         event_type="realistic_payment_simulation",
    #         transaction=transaction_obj,
    #         provider=transaction_data['provider'],
    #         metadata={
    #             'merchant_type': merchant['type'],
    #             'merchant_name': merchant['name'],
    #             'merchant_country': merchant['country'],
    #             'merchant_volume_tier': merchant.get('volume_tier', 'medium'),
    #             'commission_rate': merchant.get('commission_rate', 0.15),
    #             'business_model': merchant.get('business_model', 'commission_based'),
    #             'simulation_context': 'realistic_traffic',
    #             'time_of_day': datetime.now().hour,
    #             'day_of_week': datetime.now().weekday(),
    #             'is_peak_hour': self._is_peak_hour(merchant),
    #             'traffic_multiplier': self._calculate_traffic_multiplier(),
    #             'risk_score': risk_score,
    #             'fraud_indicators': fraud_indicators
    #         }
    #     )

    #     self.logger.log_payment_event(event)

    #     # Log routing decision if available
    #     if transaction_data.get('route_history'):
    #         latest_route = transaction_data['route_history'][-1]
    #         routing_decision = latest_route.get('routing_decision')
    #         if routing_decision:
    #             self.logger.log_routing_decision(
    #                 transaction=transaction_obj,
    #                 decision_factors=routing_decision.get('decision_factors', {}),
    #                 selected_provider=transaction_data['provider'],
    #                 alternatives=routing_decision.get('alternative_providers', [])
    #             )

    # except Exception as e:
    # Don't let logging errors break the simulation
    # pass

    def _log_payment_event(
        self,
        result: Dict[str, Any],
        payment_instrument: PaymentInstrument,
        customer: CustomerInfo,
        merchant: Dict[str, Any],
        order_id: str,
    ):
        """Log structured event for LLM training with risk scoring."""

        try:
            # Split the result into separate objects for each route history entry
            split_results = self._split_route_history(result)
            # print("result", split_results)

            # Write each split result to the file
            with open(f"logs/{self._log_filename}", "a") as f:
                for split_result in split_results:
                    f.write(json.dumps(split_result, default=str) + "\n")

        except Exception as e:
            SimulationDisplay.print_export_error(str(e))

    def _split_route_history(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split a result object into separate objects for each route history entry."""
        split_results = []

        original_transaction = result.get("transaction", {})
        route_history = original_transaction.get("route_history", [])

        if not route_history:
            return [result]

        for route_entry in route_history:
            new_result = {
                "success": route_entry.get("status") == "success",
                "provider_transaction_id": uuid.uuid4(),
                "transaction_id": original_transaction.get("id"),
                "transaction": {
                    "id": original_transaction.get("id"),
                    "amount": original_transaction.get("amount"),
                    "currency": original_transaction.get("currency"),
                    "transaction_type": original_transaction.get("transaction_type"),
                    "provider": route_entry.get("provider"),
                    "status": route_entry.get("status"),
                    "payment_instrument": original_transaction.get(
                        "payment_instrument", {}
                    ),
                    "customer_info": original_transaction.get("customer_info", {}),
                    "merchant_id": original_transaction.get("merchant_id"),
                    "order_id": original_transaction.get("order_id"),
                    "route_history": {
                        "provider": route_entry.get("provider"),
                        "status": route_entry.get("status"),
                        "timestamp": route_entry.get("timestamp"),
                        "reason": route_entry.get("reason"),
                        "processing_time": route_entry.get("processing_time"),
                        "provider_response_code": route_entry.get(
                            "provider_response_code"
                        ),
                        "provider_message": route_entry.get("provider_message"),
                        "network_response_code": route_entry.get(
                            "network_response_code"
                        ),
                        "network_latency": route_entry.get("network_latency"),
                        "retry_eligible": route_entry.get("retry_eligible"),
                        "routing_decision": route_entry.get("routing_decision", {}),
                    },
                    "timestamp": original_transaction.get("timestamp"),
                    "metadata": {
                        "success": route_entry.get("status") == "success",
                        "transaction_id": original_transaction.get("id"),
                        "provider_transaction_id": uuid.uuid4(),
                        "processing_time": route_entry.get("processing_time"),
                        "provider": route_entry.get("provider"),
                        "network_response_code": route_entry.get(
                            "network_response_code"
                        ),
                        "provider_response_code": route_entry.get(
                            "provider_response_code"
                        ),
                        "processing_fee": self._get_processing_fee(
                            route_entry, original_transaction.get("metadata", {})
                        ),
                    },
                    "risk_score": original_transaction.get("risk_score"),
                    "fraud_indicators": original_transaction.get(
                        "fraud_indicators", []
                    ),
                },
            }

            split_results.append(new_result)

        return split_results

    def _get_provider_transaction_id(self, route_entry: Dict[str, Any]) -> str:
        """Generate provider transaction ID based on route entry status."""
        return f"{uuid.uuid4()}"

    def _get_processing_fee(
        self, route_entry: Dict[str, Any], original_metadata: Dict[str, Any]
    ) -> float:
        """Get processing fee from original metadata if success, else null."""
        if route_entry.get("status") == "success":
            return original_metadata.get("processing_fee")
        return None

    def _is_peak_hour(self, merchant: Dict[str, Any]) -> bool:
        """Check if current time is peak hour for merchant."""
        hour = datetime.now().hour
        peak_start, peak_end = merchant["peak_hours"]
        return peak_start <= hour <= peak_end

    def _print_stats(self):
        """Print current simulation statistics."""
        SimulationDisplay.print_stats_summary(self.stats)

    def run_simulation(self):
        """Run the continuous payment simulation."""
        SimulationDisplay.print_header()
        SimulationDisplay.print_simulation_info()
        SimulationDisplay.print_transaction_header()

        self.running = True
        stats_interval = self.config.stats_print_interval

        try:
            while self.running:
                # Process single payment
                self.process_single_payment()

                # Print stats periodically
                if self.stats["total_payments"] % stats_interval == 0:
                    self._print_stats()

                # Calculate realistic delay
                delay = self._calculate_delay()
                time.sleep(delay)

        except KeyboardInterrupt:
            print(f"\n\n🛑 Simulation stopped by user")
            self._print_final_stats()
        except Exception as e:
            print(f"\n💥 Simulation error: {str(e)}")
            import traceback

            traceback.print_exc()
        finally:
            self.running = False

    def _print_final_stats(self):
        """Print comprehensive final statistics."""
        # Get final provider health
        health_data = self.gateway.get_provider_health()

        # Print comprehensive report
        SimulationDisplay.print_final_report(self.stats, health_data)

        # Export training data
        self._export_training_data()

    def _export_training_data(self):
        """Export logs for LLM training."""
        if not self.logger:
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            training_file = f"realistic_payment_simulation_{timestamp}.json"
            exported_file = self.logger.export_logs_for_llm_training(training_file)
            SimulationDisplay.print_export_info(exported_file)
        except Exception as e:
            SimulationDisplay.print_export_error(str(e))

    def run_quick_test(self, duration_seconds: int = 30):
        """Run a quick test simulation for specified duration."""
        print(f"🏃‍♂️ Quick Test Mode ({duration_seconds} seconds)")
        SimulationDisplay.print_transaction_header()

        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            self.process_single_payment()
            time.sleep(0.5)

        self._print_final_stats()

    def run_stress_test(self, payment_count: int = 200):
        """Run a high-volume stress test."""
        print(f"⚡ Stress Test Mode ({payment_count} payments)")
        SimulationDisplay.print_transaction_header()

        # Increase failure injection for stress test
        original_failure_prob = self.failure_injection_probability
        self.failure_injection_probability = 0.15  # Higher failure rate

        try:
            for i in range(payment_count):
                self.process_single_payment()
                if i % 50 == 0:
                    SimulationDisplay.print_progress_bar(
                        i, payment_count, "Stress Test Progress"
                    )
                time.sleep(0.1)  # Minimal delay

            SimulationDisplay.print_progress_bar(
                payment_count, payment_count, "Stress Test Progress"
            )
        finally:
            # Restore original failure probability
            self.failure_injection_probability = original_failure_prob

        self._print_final_stats()

    def run_business_hours_simulation(self):
        """Simulate traffic patterns throughout a business day."""
        print("🏢 Business Hours Simulation")
        SimulationDisplay.print_transaction_header()

        # Simulate different hours of the day with Grab-specific patterns
        business_schedule = [
            (7, 30),  # 7 AM - morning commute (transport peak)
            (9, 15),  # 9 AM - office hours start
            (12, 60),  # Noon - lunch rush (food delivery peak)
            (15, 25),  # 3 PM - afternoon lull
            (17, 40),  # 5 PM - evening commute (transport peak)
            (19, 50),  # 7 PM - dinner peak (food delivery)
            (21, 20),  # 9 PM - evening shopping
            (23, 8),  # 11 PM - night services
        ]

        for hour, payment_count in business_schedule:
            SimulationDisplay.print_time_simulation(hour, payment_count)

            for i in range(payment_count):
                # Use time-appropriate merchants
                merchant = self.merchant_generator.generate_merchant_for_time(hour)
                customer = random.choice(self.customer_pool)

                # Generate payment context
                payment_instrument = (
                    self.payment_generator.generate_payment_for_merchant_type(
                        customer, merchant["type"]
                    )
                )
                amount = self._calculate_realistic_amount(customer, merchant)
                currency = self.payment_generator.generate_currency_for_transaction(
                    customer, merchant
                )
                order_id = f"ord_{hour:02d}_{merchant['type']}_{self.fake.uuid4()[:8]}"

                try:
                    result = self.gateway.process_payment(
                        amount=amount,
                        currency=currency,
                        payment_instrument=payment_instrument,
                        customer_info=customer,
                        merchant_id=merchant["merchant_id"],
                        order_id=order_id,
                        transaction_type=TransactionType.PAYMENT,
                    )

                    self._update_stats(result, customer, merchant, payment_instrument)

                    if i % 10 == 0:  # Print every 10th transaction
                        SimulationDisplay.print_transaction(
                            result, payment_instrument, customer, merchant, order_id
                        )

                    self._log_payment_event(
                        result, payment_instrument, customer, merchant, order_id
                    )

                except Exception as e:
                    self.stats["failed_payments"] += 1
                    self.stats["total_payments"] += 1

                time.sleep(random.uniform(0.1, 0.5))

            self._print_stats()

        self._print_final_stats()

    def run_high_failure_simulation(self):
        """Run simulation with intentionally high failure rates for testing recovery."""
        print("🔥 HIGH FAILURE MODE - Testing Recovery Agent")
        print("This mode generates 40%+ failure rate to test autonomous recovery")
        print("=" * 60)

        # Store original settings
        original_failure_prob = self.failure_injection_probability

        # Increase failure rates dramatically
        self.failure_injection_probability = 0.4  # 40% base failure rate

        # Configure all providers for higher failures
        for provider_name in ["stripe", "adyen", "paypal", "razorpay"]:
            self.gateway.configure_provider(
                provider_name, success_rate=0.6
            )  # 60% success instead of 85-90%

        # Inject multiple concurrent failures
        failure_scenarios = [
            "stripe_maintenance",
            "paypal_low_success",
            "adyen_high_latency",
        ]
        for scenario in failure_scenarios:
            self.gateway.simulate_scenario(scenario)
            print(f"🔥 Activated {scenario}")

        try:
            SimulationDisplay.print_transaction_header()
            self.running = True
            stats_interval = 25  # More frequent stats

            while self.running:
                # Process payment with high failure context
                self.process_single_payment()

                # Print stats more frequently
                if self.stats["total_payments"] % stats_interval == 0:
                    self._print_stats()

                    # Show current failure rate
                    total = self.stats["total_payments"]
                    failures = self.stats["failed_payments"]
                    if total > 0:
                        failure_rate = (failures / total) * 100
                        print(f"🔥 Current Failure Rate: {failure_rate:.1f}%")

                # Shorter delays for faster failure demonstration
                delay = self._calculate_delay() * 0.5  # Half normal delay
                time.sleep(delay)

        except KeyboardInterrupt:
            print(f"\n\n🛑 High failure simulation stopped")
        finally:
            # Restore original settings
            self.failure_injection_probability = original_failure_prob
            self.gateway.simulate_scenario("reset_all")
            self.running = False
            self._print_final_stats()
        """Generate a sample LLM training prompt from simulation data."""
        total = self.stats.get("total_payments", 0)
        if total == 0:
            return "No payment data available for analysis."

        success_rate = (self.stats.get("successful_payments", 0) / total) * 100

        prompt = f"""
Based on the following Grab payment ecosystem performance data, analyze the system health and recommend actions:

SYSTEM METRICS:
- Total Payments: {total:,}
- Success Rate: {success_rate:.1f}%
- Failed Payments: {self.stats.get('failed_payments', 0)}

GRAB ECOSYSTEM DISTRIBUTION:
- By Network: {self.stats.get('by_network', {})}
- By Method: {self.stats.get('by_method', {})}
- By Region: {self.stats.get('by_region', {})}
- By Service Type: {self.stats.get('by_merchant_type', {})}

FAILURE SCENARIOS: {len(self.stats.get('scenarios_triggered', []))} triggered

GRAB-SPECIFIC ANALYSIS QUESTIONS:
1. Is the {success_rate:.1f}% success rate acceptable for Grab's payment ecosystem?
2. Which Grab services (transport/food/mart) show the highest failure rates?
3. Are there regional patterns suggesting routing optimizations for SEA markets?
4. What preventive measures should be implemented for peak hours?
5. Which providers should be prioritized for different Grab service types?
6. How can we optimize for mobile-first Southeast Asian payment preferences?

Provide a detailed analysis with specific recommendations for improving Grab's payment success rates.
"""
        return prompt
