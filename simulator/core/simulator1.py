"""
Core payment gateway simulator for realistic transaction generation.
"""

import sys
import os
import time
import random
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add faker for realistic data generation
try:
    from faker import Faker
    from faker.providers import credit_card, company, internet, phone_number
except ImportError:
    print("Installing faker library.")
    os.system("pip install faker")
    from faker import Faker
    from faker.providers import credit_card, company, internet, phone_number

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from payment_gateway.gateway.payment_gateway import PaymentGateway
from payment_gateway.core.enums import (
    RoutingStrategy, CardNetwork, PaymentMethod, Currency, 
    Region, RiskLevel, TransactionType
)
from payment_gateway.core.models import PaymentInstrument, CustomerInfo, Transaction as TransactionModel
from payment_gateway.logging.structured_logger import StructuredLogger

# Import simulation components
from data.customer_generator import CustomerGenerator
from data.merchant_generator import MerchantGenerator
from data.payment_generator import PaymentInstrumentGenerator
from utils.display import SimulationDisplay, MetricsFormatter
from .config import SimulationConfig, FAILURE_SCENARIOS


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
        self.gateway = PaymentGateway()
        try:
            self.logger = StructuredLogger()
        except Exception as e:
            print(f"Warning: Could not initialize structured logger: {e}")
            self.logger = None
        
        # Simulation control
        self.running = False
        self.stats = {
            'total_payments': 0,
            'successful_payments': 0,
            'failed_payments': 0,
            'by_network': {},
            'by_method': {},
            'by_region': {},
            'by_merchant_type': {},
            'by_amount_range': {},
            'scenarios_triggered': []
        }
        
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
            len(self.customer_pool), 
            len(self.merchant_pool)
        )
    
    def process_single_payment(self):
        """Process a single realistic payment transaction."""
        try:
            # Select random customer and merchant
            customer = random.choice(self.customer_pool)
            merchant = random.choice(self.merchant_pool)
            
            # Generate realistic payment context
            payment_instrument = self.payment_generator.generate_payment_for_merchant_type(
                customer, merchant['type']
            )
            amount = self._calculate_realistic_amount(customer, merchant)
            currency = self.payment_generator.generate_currency_for_transaction(customer, merchant)
            
            # Generate order ID and other metadata
            order_id = f"ord_{merchant['type']}_{self.fake.uuid4()[:12]}"
            
            # Occasionally inject failures
            if self._should_inject_failure():
                self._inject_random_failure()
            
            # Process payment
            result = self.gateway.process_payment(
                amount=amount,
                currency=currency,
                payment_instrument=payment_instrument,
                customer_info=customer,
                merchant_id=merchant['merchant_id'],
                order_id=order_id,
                transaction_type=TransactionType.PAYMENT
            )
            
            # Update statistics
            self._update_stats(result, customer, merchant, payment_instrument)
            
            # Print transaction summary
            SimulationDisplay.print_transaction(
                result, payment_instrument, customer, merchant, order_id
            )
            
            # Log structured event for LLM training
            self._log_payment_event(result, payment_instrument, customer, merchant, order_id)
        
        except Exception as e:
            print(f"❌ Payment processing error: {str(e)}")
            self.stats['failed_payments'] += 1
            self.stats['total_payments'] += 1
    
    def _calculate_realistic_amount(self, customer: CustomerInfo, merchant: Dict[str, Any]) -> float:
        """Calculate realistic transaction amounts based on context."""
        base_amount = merchant['avg_transaction_value']
        
        # Customer behavior patterns
        if customer.risk_level == RiskLevel.HIGH:
            # High-risk customers tend to have unusual amounts
            base_amount *= random.choice([0.1, 0.2, 5.0, 10.0])
        elif customer.successful_payments > 100:
            # Loyal customers tend to spend more
            base_amount *= random(1.2, 2.5)
        
        # Time-based patterns
        hour = datetime.now().hour
        peak_start, peak_end = merchant['peak_hours']
        if peak_start <= hour <= peak_end:
            base_amount *= random(1.1, 1.4)  # Higher amounts during peak
        
        # Merchant type specific adjustments
        if merchant['type'] == 'financial_services':
            # Financial services have wider range
            base_amount *= random(0.5, 5.0)
        elif merchant['type'] == 'enterprise_b2b':
            # B2B transactions are typically larger
            base_amount *= random(2.0, 10.0)
        
        # Add realistic variance
        variance = random(0.7, 1.8)
        amount = base_amount * variance
        
        # Round to realistic values based on amount
        if amount < 10:
            return round(amount, 2)
        elif amount < 100:
            return round(amount / 5) * 5  # Round to nearest $5
        else:
            return round(amount / 10) * 10  # Round to nearest $10
    
    def _should_inject_failure(self) -> bool:
        """Decide whether to inject a failure scenario."""
        return random.random() < self.failure_injection_probability
    
    def _inject_random_failure(self):
        """Randomly inject failure scenarios to simulate real-world issues."""
        scenario = random.choice(FAILURE_SCENARIOS)
        result = self.gateway.simulate_scenario(scenario)
        
        if result['success']:
            self.stats['scenarios_triggered'].append({
                'scenario': scenario,
                'timestamp': datetime.now().isoformat(),
                'message': result['message']
            })
            SimulationDisplay.print_scenario_injection(scenario, result['message'])
            
            # Schedule recovery after random time
            recovery_time = random(*self.config.failure_recovery_time_range)
            threading.Timer(recovery_time, self._recover_from_failure).start()
    
    def _recover_from_failure(self):
        """Recover from injected failure scenarios."""
        result = self.gateway.simulate_scenario('reset_all')
        if result['success']:
            SimulationDisplay.print_scenario_recovery()
    
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
        multiplier *= random(0.8, 1.2)
        
        return multiplier
    
    def _calculate_delay(self) -> float:
        """Calculate realistic delay between payments."""
        traffic_multiplier = self._calculate_traffic_multiplier()
        
        # Base delay (seconds between payments)
        base_delay = self.config.base_delay
        
        # Adjust based on traffic (higher traffic = shorter delays)
        delay = base_delay / traffic_multiplier
        
        # Add realistic variance
        delay *= random(0.5, 2.0)
        
        # Ensure minimum and maximum delays
        return max(self.config.min_delay, min(delay, self.config.max_delay))
    
    def _update_stats(self, transaction_result: Dict[str, Any], customer: CustomerInfo, 
                     merchant: Dict[str, Any], payment_instrument: PaymentInstrument):
        """Update simulation statistics."""
        self.stats['total_payments'] += 1
        
        if transaction_result['success']:
            self.stats['successful_payments'] += 1
        else:
            self.stats['failed_payments'] += 1
        
        # Track by network
        if payment_instrument.network:
            network = payment_instrument.network.value
            self.stats['by_network'][network] = self.stats['by_network'].get(network, 0) + 1
        
        # Track by method
        method = payment_instrument.method.value
        self.stats['by_method'][method] = self.stats['by_method'].get(method, 0) + 1
        
        # Track by region
        region = customer.region.value
        self.stats['by_region'][region] = self.stats['by_region'].get(region, 0) + 1
        
        # Track by merchant type
        merchant_type = merchant['type']
        self.stats['by_merchant_type'][merchant_type] = self.stats['by_merchant_type'].get(merchant_type, 0) + 1
        
        # Track by amount range
        amount = transaction_result['transaction']['amount']
        if amount < 25:
            range_key = '0-25'
        elif amount < 100:
            range_key = '25-100'
        elif amount < 500:
            range_key = '100-500'
        else:
            range_key = '500+'
        
        self.stats['by_amount_range'][range_key] = self.stats['by_amount_range'].get(range_key, 0) + 1
    
    def _log_payment_event(self, result: Dict[str, Any], payment_instrument: PaymentInstrument,
                          customer: CustomerInfo, merchant: Dict[str, Any], order_id: str):
        """Log structured event for LLM training."""
        if not self.logger:
            return
        
        try:
            transaction_data = result['transaction']
            
            # Create transaction model for logging
            transaction_obj = TransactionModel(
                id=transaction_data['id'],
                amount=transaction_data['amount'],
                currency=Currency(transaction_data['currency']),
                transaction_type=TransactionType.PAYMENT,
                provider=transaction_data['provider'],
                status=transaction_data['status'],
                payment_instrument=payment_instrument,
                customer_info=customer,
                merchant_id=merchant['merchant_id'],
                order_id=order_id
            )
            
            from payment_gateway.core.models import PaymentEvent
            event = PaymentEvent(
                event_type="realistic_payment_simulation",
                transaction=transaction_obj,
                provider=transaction_data['provider'],
                metadata={
                    'merchant_type': merchant['type'],
                    'merchant_name': merchant['name'],
                    'merchant_country': merchant['country'],
                    'merchant_volume_tier': merchant.get('volume_tier', 'medium'),
                    'commission_rate': merchant.get('commission_rate', 0.15),
                    'business_model': merchant.get('business_model', 'commission_based'),
                    'simulation_context': 'realistic_traffic',
                    'time_of_day': datetime.now().hour,
                    'day_of_week': datetime.now().weekday(),
                    'is_peak_hour': self._is_peak_hour(merchant),
                    'traffic_multiplier': self._calculate_traffic_multiplier()
                }
            )
            
            self.logger.log_payment_event(event)
            
            # Log routing decision if available
            if transaction_data.get('route_history'):
                latest_route = transaction_data['route_history'][-1]
                routing_decision = latest_route.get('routing_decision')
                if routing_decision:
                    self.logger.log_routing_decision(
                        transaction=transaction_obj,
                        decision_factors=routing_decision.get('decision_factors', {}),
                        selected_provider=transaction_data['provider'],
                        alternatives=routing_decision.get('alternative_providers', [])
                    )
        
        except Exception as e:
            # Don't let logging errors break the simulation
            pass
    
    def _is_peak_hour(self, merchant: Dict[str, Any]) -> bool:
        """Check if current time is peak hour for merchant."""
        hour = datetime.now().hour
        peak_start, peak_end = merchant['peak_hours']
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
                if self.stats['total_payments'] % stats_interval == 0:
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
            training_file = f'realistic_payment_simulation_{timestamp}.json'
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
                    SimulationDisplay.print_progress_bar(i, payment_count, "Stress Test Progress")
                time.sleep(0.1)  # Minimal delay
            
            SimulationDisplay.print_progress_bar(payment_count, payment_count, "Stress Test Progress")
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
            (7, 30),   # 7 AM - morning commute (transport peak)
            (9, 15),   # 9 AM - office hours start
            (12, 60),  # Noon - lunch rush (food delivery peak)
            (15, 25),  # 3 PM - afternoon lull
            (17, 40),  # 5 PM - evening commute (transport peak)
            (19, 50),  # 7 PM - dinner peak (food delivery)
            (21, 20),  # 9 PM - evening shopping
            (23, 8)    # 11 PM - night services
        ]
        
        for hour, payment_count in business_schedule:
            SimulationDisplay.print_time_simulation(hour, payment_count)
            
            for i in range(payment_count):
                # Use time-appropriate merchants
                merchant = self.merchant_generator.generate_merchant_for_time(hour)
                customer = random.choice(self.customer_pool)
                
                # Generate payment context
                payment_instrument = self.payment_generator.generate_payment_for_merchant_type(
                    customer, merchant['type']
                )
                amount = self._calculate_realistic_amount(customer, merchant)
                currency = self.payment_generator.generate_currency_for_transaction(customer, merchant)
                order_id = f"ord_{hour:02d}_{merchant['type']}_{self.fake.uuid4()[:8]}"
                
                try:
                    result = self.gateway.process_payment(
                        amount=amount,
                        currency=currency,
                        payment_instrument=payment_instrument,
                        customer_info=customer,
                        merchant_id=merchant['merchant_id'],
                        order_id=order_id,
                        transaction_type=TransactionType.PAYMENT
                    )
                    
                    self._update_stats(result, customer, merchant, payment_instrument)
                    
                    if i % 10 == 0:  # Print every 10th transaction
                        SimulationDisplay.print_transaction(
                            result, payment_instrument, customer, merchant, order_id
                        )
                    
                    self._log_payment_event(result, payment_instrument, customer, merchant, order_id)
                
                except Exception as e:
                    self.stats['failed_payments'] += 1
                    self.stats['total_payments'] += 1
                
                time.sleep(random(0.1, 0.5))
            
            self._print_stats()
        
        self._print_final_stats()
    
    def generate_training_prompt(self) -> str:
        """Generate a sample LLM training prompt from simulation data."""
        total = self.stats.get('total_payments', 0)
        if total == 0:
            return "No payment data available for analysis."
        
        success_rate = (self.stats.get('successful_payments', 0) / total) * 100
        
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