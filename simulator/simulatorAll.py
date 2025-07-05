#!/usr/bin/env python3
"""
Realistic Payment Gateway Simulator

This script simulates a real-world payment gateway with:
- Realistic customer data using Faker
- All payment methods and card networks
- Dynamic failure scenarios
- Variable load patterns
- Business-realistic transaction patterns
- Comprehensive logging for LLM training

Run until Ctrl+C to generate continuous realistic payment data.
"""

import sys
import os
import time
import random
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any
import signal

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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from payment_gateway.gateway.payment_gateway import PaymentGateway
from payment_gateway.core.enums import (
    RoutingStrategy,
    CardNetwork,
    PaymentMethod,
    Currency,
    Region,
    RiskLevel,
    TransactionType,
)
from payment_gateway.core.models import PaymentInstrument, CustomerInfo
from payment_gateway.logging.structured_logger import StructuredLogger


class RealisticPaymentSimulator:
    """Comprehensive payment gateway simulator with realistic data patterns."""

    def __init__(self):
        """Initialize the simulator with realistic data generators."""
        self.fake = Faker()
        self.fake.add_provider(credit_card)
        self.fake.add_provider(company)
        self.fake.add_provider(internet)
        self.fake.add_provider(phone_number)

        # Initialize gateway and logger
        self.gateway = PaymentGateway()
        self.logger = StructuredLogger()

        # Simulation control
        self.running = False
        self.stats = {
            "total_payments": 0,
            "successful_payments": 0,
            "failed_payments": 0,
            "by_network": {},
            "by_method": {},
            "by_region": {},
            "by_amount_range": {},
            "scenarios_triggered": [],
        }

        # Realistic patterns
        self.business_hours = (9, 17)  # 9 AM to 5 PM peak
        self.weekend_multiplier = 0.6  # 60% traffic on weekends
        self.failure_injection_probability = 0.8  # 5% chance of injecting failures

        # Customer database simulation
        self.customer_pool = self._generate_customer_pool(1000)
        self.merchant_pool = self._generate_merchant_pool(50)

        print("🎭 Realistic Payment Gateway Simulator Initialized")
        print(
            f"📊 Generated {len(self.customer_pool)} customers and {len(self.merchant_pool)} merchants"
        )

    def _generate_customer_pool(self, count: int) -> List[CustomerInfo]:
        """Generate a pool of realistic customers."""
        customers = []

        for _ in range(count):
            # Regional distribution based on real world
            region_weights = [
                (Region.NORTH_AMERICA, 0.3),
                (Region.EUROPE, 0.25),
                (Region.SOUTHEAST_ASIA, 0.2),
                (Region.ASIA_PACIFIC, 0.15),
                (Region.LATIN_AMERICA, 0.1),
            ]
            region = random.choices(
                [r[0] for r in region_weights], weights=[r[1] for r in region_weights]
            )[0]

            # Country mapping
            country_map = {
                Region.NORTH_AMERICA: ["US", "CA", "MX"],
                Region.EUROPE: ["GB", "DE", "FR", "IT", "ES"],
                Region.SOUTHEAST_ASIA: ["SG", "MY", "TH", "ID", "VN", "PH"],
                Region.ASIA_PACIFIC: ["JP", "KR", "AU", "NZ"],
                Region.LATIN_AMERICA: ["BR", "AR", "CL", "CO"],
            }
            country = random.choice(country_map[region])

            # Risk level distribution (realistic)
            risk_weights = [
                (RiskLevel.LOW, 0.7),
                (RiskLevel.MEDIUM, 0.25),
                (RiskLevel.HIGH, 0.05),
            ]
            risk_level = random.choices(
                [r[0] for r in risk_weights], weights=[r[1] for r in risk_weights]
            )[0]

            customer = CustomerInfo(
                customer_id=f"cust_{self.fake.uuid4()[:8]}",
                email=self.fake.email(),
                phone=self.fake.phone_number(),
                country=country,
                region=region,
                risk_level=risk_level,
                successful_payments=(
                    random.randint(0, 200)
                    if risk_level == RiskLevel.LOW
                    else random.randint(0, 50)
                ),
                previous_failures=(
                    random.randint(0, 3)
                    if risk_level == RiskLevel.HIGH
                    else random.randint(0, 1)
                ),
                preferred_providers=random.sample(
                    ["stripe", "adyen", "paypal", "razorpay"], k=random.randint(1, 2)
                ),
            )
            customers.append(customer)

        return customers

    def _generate_merchant_pool(self, count: int) -> List[Dict[str, Any]]:
        """Generate a pool of realistic merchants."""
        merchants = []

        merchant_types = [
            ("transport", 0.35),  # GrabCar, GrabBike, GrabTaxi, GrabShare
            ("food_delivery", 0.25),  # GrabFood restaurants and merchants
            ("mart_grocery", 0.15),  # GrabMart - groceries and essentials
            ("express_delivery", 0.10),  # GrabExpress - courier and parcels
            ("financial_services", 0.08),  # GrabPay, PayLater, GrabFin
            ("rewards_partners", 0.05),  # GrabRewards partner merchants
            ("enterprise_b2b", 0.02),  # GrabForBusiness services
        ]

        for _ in range(count):
            merchant_type = random.choices(
                [m[0] for m in merchant_types], weights=[m[1] for m in merchant_types]
            )[0]

            merchant = {
                "merchant_id": f"merch_{self.fake.uuid4()[:8]}",
                "name": self.fake.company(),
                "type": merchant_type,
                "country": random.choice(["US", "GB", "SG", "DE", "AU"]),
                "avg_transaction_value": self._get_merchant_avg_amount(merchant_type),
                "peak_hours": self._get_merchant_peak_hours(merchant_type),
            }
            merchants.append(merchant)

        return merchants

    def _get_merchant_avg_amount(self, merchant_type: str) -> float:
        """Get realistic average transaction amounts by Grab merchant type."""
        amounts = {
            "transport": (8, 25),  # Typical ride fares
            "food_delivery": (12, 35),  # Meal orders
            "mart_grocery": (20, 80),  # Grocery shopping
            "express_delivery": (5, 20),  # Courier services
            "financial_services": (50, 500),  # Loan payments, top-ups
            "rewards_partners": (15, 100),  # Partner merchant purchases
            "enterprise_b2b": (100, 2000),  # Corporate services
        }
        min_amt, max_amt = amounts.get(merchant_type, (10, 50))
        return random(min_amt, max_amt)

    def _get_merchant_peak_hours(self, merchant_type: str) -> tuple:
        """Get peak hours by Grab merchant type."""
        peaks = {
            "transport": (7, 9),  # Morning commute + evening (17-19)
            "food_delivery": (11, 14),  # Lunch + dinner (18-21)
            "mart_grocery": (17, 21),  # After work shopping
            "express_delivery": (9, 17),  # Business hours
            "financial_services": (10, 16),  # Banking hours
            "rewards_partners": (12, 20),  # Shopping hours
            "enterprise_b2b": (9, 17),  # Business hours
        }
        return peaks.get(merchant_type, (9, 17))

    def _generate_realistic_payment_instrument(
        self, customer: CustomerInfo
    ) -> PaymentInstrument:
        """Generate realistic payment instruments based on customer region."""

        # Regional payment method preferences
        method_preferences = {
            Region.NORTH_AMERICA: [
                (PaymentMethod.CARD, 0.6),
                (PaymentMethod.DIGITAL_WALLET, 0.3),
                (PaymentMethod.BANK_TRANSFER, 0.1),
            ],
            Region.EUROPE: [
                (PaymentMethod.CARD, 0.5),
                (PaymentMethod.BANK_TRANSFER, 0.3),
                (PaymentMethod.DIGITAL_WALLET, 0.2),
            ],
            Region.SOUTHEAST_ASIA: [
                (PaymentMethod.DIGITAL_WALLET, 0.4),
                (PaymentMethod.CARD, 0.35),
                (PaymentMethod.BANK_TRANSFER, 0.25),
            ],
            Region.ASIA_PACIFIC: [
                (PaymentMethod.CARD, 0.45),
                (PaymentMethod.DIGITAL_WALLET, 0.35),
                (PaymentMethod.BANK_TRANSFER, 0.2),
            ],
            Region.LATIN_AMERICA: [
                (PaymentMethod.CARD, 0.4),
                (PaymentMethod.BANK_TRANSFER, 0.35),
                (PaymentMethod.DIGITAL_WALLET, 0.25),
            ],
        }

        preferences = method_preferences.get(
            customer.region, method_preferences[Region.NORTH_AMERICA]
        )
        payment_method = random.choices(
            [p[0] for p in preferences], weights=[p[1] for p in preferences]
        )[0]

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

        # Regional card network preferences
        network_preferences = {
            Region.NORTH_AMERICA: [
                (CardNetwork.VISA, 0.4),
                (CardNetwork.MASTERCARD, 0.35),
                (CardNetwork.AMEX, 0.15),
                (CardNetwork.DISCOVER, 0.1),
            ],
            Region.EUROPE: [
                (CardNetwork.VISA, 0.45),
                (CardNetwork.MASTERCARD, 0.45),
                (CardNetwork.AMEX, 0.08),
                (CardNetwork.DINERS, 0.02),
            ],
            Region.SOUTHEAST_ASIA: [
                (CardNetwork.VISA, 0.4),
                (CardNetwork.MASTERCARD, 0.35),
                (CardNetwork.UNIONPAY, 0.15),
                (CardNetwork.JCB, 0.1),
            ],
            Region.ASIA_PACIFIC: [
                (CardNetwork.VISA, 0.35),
                (CardNetwork.MASTERCARD, 0.3),
                (CardNetwork.JCB, 0.2),
                (CardNetwork.AMEX, 0.15),
            ],
        }

        preferences = network_preferences.get(
            customer.region, network_preferences[Region.NORTH_AMERICA]
        )
        network = random.choices(
            [p[0] for p in preferences], weights=[p[1] for p in preferences]
        )[0]

        # Generate card details
        card_number = self.fake.credit_card_number(
            card_type=(
                network.value.lower() if network.value.lower() != "amex" else "amex"
            )
        )

        return PaymentInstrument(
            method=PaymentMethod.CARD,
            network=network,
            last_four=card_number[-4:],
            expiry_month=random.randint(1, 12),
            expiry_year=random.randint(2024, 2030),
            country_code=customer.country,
            issuer=self._get_realistic_issuer(customer.country, network),
            brand=f"{network.value.lower()}_{'credit' if random.random() > 0.3 else 'debit'}",
        )

    def _generate_wallet_instrument(self, customer: CustomerInfo) -> PaymentInstrument:
        """Generate digital wallet payment instrument."""

        wallet_preferences = {
            Region.NORTH_AMERICA: ["apple_pay", "google_pay", "paypal", "venmo"],
            Region.EUROPE: ["apple_pay", "google_pay", "paypal", "klarna"],
            Region.SOUTHEAST_ASIA: ["grabpay", "google_pay", "apple_pay", "touchngo"],
            Region.ASIA_PACIFIC: ["apple_pay", "google_pay", "alipay", "wechat_pay"],
            Region.LATIN_AMERICA: ["mercado_pago", "google_pay", "apple_pay", "pix"],
        }

        wallets = wallet_preferences.get(customer.region, ["apple_pay", "google_pay"])
        wallet_type = random.choice(wallets)

        return PaymentInstrument(
            method=PaymentMethod.DIGITAL_WALLET,
            wallet_type=wallet_type,
            country_code=customer.country,
        )

    def _generate_bank_instrument(self, customer: CustomerInfo) -> PaymentInstrument:
        """Generate bank transfer payment instrument."""
        return PaymentInstrument(
            method=PaymentMethod.BANK_TRANSFER,
            country_code=customer.country,
            issuer=f"{self.fake.company()} Bank",
        )

    def _generate_bnpl_instrument(self, customer: CustomerInfo) -> PaymentInstrument:
        """Generate Buy Now Pay Later payment instrument."""
        return PaymentInstrument(
            method=PaymentMethod.BUY_NOW_PAY_LATER,
            country_code=customer.country,
            brand=random.choice(["klarna", "afterpay", "affirm", "sezzle"]),
        )

    def _get_realistic_issuer(self, country: str, network: CardNetwork) -> str:
        """Get realistic card issuers by country and network."""
        issuers = {
            "US": [
                "Chase Bank",
                "Bank of America",
                "Wells Fargo",
                "Citi",
                "Capital One",
            ],
            "GB": ["Barclays", "HSBC", "Lloyds", "NatWest", "Santander"],
            "SG": ["DBS Bank", "OCBC Bank", "UOB", "Standard Chartered", "Maybank"],
            "DE": ["Deutsche Bank", "Commerzbank", "HypoVereinsbank", "Postbank"],
            "JP": ["MUFG Bank", "Sumitomo Mitsui", "Mizuho Bank", "Rakuten Bank"],
            "AU": ["Commonwealth Bank", "Westpac", "ANZ", "NAB"],
        }

        country_issuers = issuers.get(
            country, ["Generic Bank", "Local Bank", "Regional Bank"]
        )
        return random.choice(country_issuers)

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
            base_amount *= random(1.2, 2.5)

        # Time-based patterns
        hour = datetime.now().hour
        if merchant["peak_hours"][0] <= hour <= merchant["peak_hours"][1]:
            base_amount *= random(1.1, 1.4)  # Higher amounts during peak

        # Add realistic variance
        variance = random(0.7, 1.8)
        amount = base_amount * variance

        # Round to realistic values
        if amount < 10:
            return round(amount, 2)
        elif amount < 100:
            return round(amount / 5) * 5  # Round to nearest $5
        else:
            return round(amount / 10) * 10  # Round to nearest $10

    def _select_realistic_currency(
        self, customer: CustomerInfo, merchant: Dict[str, Any]
    ) -> Currency:
        """Select realistic currency based on customer and merchant location."""

        # Primary currency by region
        primary_currencies = {
            Region.NORTH_AMERICA: Currency.USD,
            Region.EUROPE: Currency.EUR,
            Region.SOUTHEAST_ASIA: Currency.SGD,
            Region.ASIA_PACIFIC: Currency.USD,  # International transactions
            Region.LATIN_AMERICA: Currency.USD,
        }

        # Local currencies by country
        local_currencies = {
            "GB": Currency.GBP,
            "SG": Currency.SGD,
            "MY": Currency.MYR,
            "TH": Currency.THB,
            "ID": Currency.IDR,
            "VN": Currency.VND,
            "PH": Currency.PHP,
        }

        # 80% chance of using local currency, 20% chance of USD/EUR for international
        if random.random() < 0.8:
            return local_currencies.get(
                customer.country, primary_currencies[customer.region]
            )
        else:
            return random.choice([Currency.USD, Currency.EUR])

    def _should_inject_failure(self) -> bool:
        """Decide whether to inject a failure scenario."""
        return random.random() < self.failure_injection_probability

    def _inject_random_failure(self):
        """Randomly inject failure scenarios to simulate real-world issues."""
        scenarios = [
            "stripe_maintenance",
            "adyen_high_latency",
            "paypal_low_success",
            "razorpay_rate_limit",
        ]

        scenario = random.choice(scenarios)
        result = self.gateway.simulate_scenario(scenario)

        if result["success"]:
            self.stats["scenarios_triggered"].append(
                {
                    "scenario": scenario,
                    "timestamp": datetime.now().isoformat(),
                    "message": result["message"],
                }
            )
            print(f"🔥 Injected failure scenario: {scenario}")

            # Schedule recovery after random time
            recovery_time = random(10, 60)  # 10-60 seconds
            threading.Timer(recovery_time, self._recover_from_failure).start()

    def _recover_from_failure(self):
        """Recover from injected failure scenarios."""
        result = self.gateway.simulate_scenario("reset_all")
        if result["success"]:
            print(f"✅ Recovered from failure scenarios")

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

        # Add some randomness
        multiplier *= random(0.8, 1.2)

        return multiplier

    def _calculate_delay(self) -> float:
        """Calculate realistic delay between payments."""
        traffic_multiplier = self._calculate_traffic_multiplier()

        # Base delay (seconds between payments)
        base_delay = 2.0

        # Adjust based on traffic (higher traffic = shorter delays)
        delay = base_delay / traffic_multiplier

        # Add realistic variance
        delay *= random(0.5, 2.0)

        # Ensure minimum and maximum delays
        return min(0.1, min(delay, 10.0))

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

    def _print_stats(self):
        """Print current simulation statistics."""
        total = self.stats["total_payments"]
        if total == 0:
            return

        success_rate = (self.stats["successful_payments"] / total) * 100

        print(f"\n📊 SIMULATION STATS (Total: {total} payments)")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Successful: {self.stats['successful_payments']}")
        print(f"   Failed: {self.stats['failed_payments']}")

        if self.stats["by_network"]:
            print(f"   By Network: {dict(list(self.stats['by_network'].items())[:3])}")

        if self.stats["by_method"]:
            print(f"   By Method: {self.stats['by_method']}")

        if self.stats["by_region"]:
            print(f"   By Region: {dict(list(self.stats['by_region'].items())[:3])}")

        if self.stats["scenarios_triggered"]:
            recent_scenarios = [
                s["scenario"] for s in self.stats["scenarios_triggered"][-3:]
            ]
            print(f"   Recent Failures: {recent_scenarios}")

    def process_single_payment(self):
        """Process a single realistic payment transaction."""
        try:
            # Select random customer and merchant
            customer = random.choice(self.customer_pool)
            merchant = random.choice(self.merchant_pool)

            # Generate realistic payment context
            payment_instrument = self._generate_realistic_payment_instrument(customer)
            amount = self._calculate_realistic_amount(customer, merchant)
            currency = self._select_realistic_currency(customer, merchant)

            # Generate order ID and other metadata
            order_id = f"ord_{self.fake.uuid4()[:12]}"

            # Occasionally inject failures
            if self._should_inject_failure():
                self._inject_random_failure()

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
            transaction = result["transaction"]
            status_emoji = "✅" if result["success"] else "❌"

            print(
                f"{status_emoji} {currency.value} {amount:>8.2f} | "
                f"{payment_instrument.method.value:>12} | "
                f"{transaction['provider']:>8} | "
                f"{customer.region.value:>15} | "
                f"Order: {order_id}"
            )

            # Log structured event for LLM training
            if hasattr(self.logger, "log_payment_event"):
                from payment_gateway.core.models import (
                    PaymentEvent,
                    Transaction as TransactionModel,
                )

                # Create transaction model for logging
                transaction_obj = TransactionModel(
                    id=transaction["id"],
                    amount=amount,
                    currency=currency,
                    transaction_type=TransactionType.PAYMENT,
                    provider=transaction["provider"],
                    status=transaction["status"],
                    payment_instrument=payment_instrument,
                    customer_info=customer,
                    merchant_id=merchant["merchant_id"],
                    order_id=order_id,
                )

                event = PaymentEvent(
                    event_type="realistic_payment_simulation",
                    transaction=transaction_obj,
                    provider=transaction["provider"],
                    metadata={
                        "merchant_type": merchant["type"],
                        "simulation_context": "realistic_traffic",
                    },
                )

                self.logger.log_payment_event(event)

        except Exception as e:
            print(f"❌ Payment processing error: {str(e)}")
            self.stats["failed_payments"] += 1

    def run_simulation(self):
        """Run the continuous payment simulation."""
        print(f"\n🚀 Starting Realistic Payment Gateway Simulation")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💳 Press Ctrl+C to stop simulation\n")

        print(
            "Status | Amount    | Method       | Provider | Region         | Order ID"
        )
        print("-" * 85)

        self.running = True
        stats_interval = 50  # Print stats every 50 transactions

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
        print(f"\n{'='*80}")
        print(f" FINAL SIMULATION REPORT")
        print(f"{'='*80}")

        total = self.stats["total_payments"]
        if total == 0:
            print("No payments processed.")
            return

        success_rate = (self.stats["successful_payments"] / total) * 100

        print(f"\n📈 OVERALL PERFORMANCE:")
        print(f"   Total Payments Processed: {total:,}")
        print(
            f"   Successful Payments: {self.stats['successful_payments']:,} ({success_rate:.1f}%)"
        )
        print(
            f"   Failed Payments: {self.stats['failed_payments']:,} ({100-success_rate:.1f}%)"
        )

        print(f"\n🏦 BY CARD NETWORK:")
        for network, count in sorted(
            self.stats["by_network"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total) * 100
            print(f"   {network:>12}: {count:>4} ({percentage:>5.1f}%)")

        print(f"\n💳 BY PAYMENT METHOD:")
        for method, count in sorted(
            self.stats["by_method"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total) * 100
            print(f"   {method:>15}: {count:>4} ({percentage:>5.1f}%)")

        print(f"\n🌍 BY REGION:")
        for region, count in sorted(
            self.stats["by_region"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total) * 100
            print(f"   {region:>15}: {count:>4} ({percentage:>5.1f}%)")

        print(f"\n💰 BY AMOUNT RANGE:")
        for range_key, count in sorted(
            self.stats["by_amount_range"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total) * 100
            print(f"   ${range_key:>8}: {count:>4} ({percentage:>5.1f}%)")

        if self.stats["scenarios_triggered"]:
            print(
                f"\n🔥 FAILURE SCENARIOS TRIGGERED: {len(self.stats['scenarios_triggered'])}"
            )
            for scenario in self.stats["scenarios_triggered"][-5:]:  # Show last 5
                timestamp = datetime.fromisoformat(scenario["timestamp"]).strftime(
                    "%H:%M:%S"
                )
                print(f"   {timestamp}: {scenario['scenario']}")

        # Provider health summary
        print(f"\n🏥 FINAL PROVIDER HEALTH:")
        health_data = self.gateway.get_provider_health()
        for provider, health in health_data.items():
            success_rate = health["success_rate"] * 100
            latency = health["avg_latency"]
            status = "🟢" if health["is_healthy"] else "🔴"
            print(
                f"   {status} {provider:>8}: {success_rate:>5.1f}% success, {latency:>6.0f}ms avg"
            )

        print(f"\n📁 TRAINING DATA:")
        print(f"   Structured logs saved to: ./logs/")
        print(f"   Use these logs to train your LLM diagnostic brain!")

        # Export final training data
        try:
            training_file = self.logger.export_logs_for_llm_training(
                "realistic_payment_simulation.json"
            )
            print(f"   Exported training dataset: {training_file}")
        except Exception as e:
            print(f"   Export error: {e}")


def setup_signal_handlers(simulator):
    """Setup signal handlers for graceful shutdown."""

    def signal_handler(signum, frame):
        print(f"\n🔄 Received signal {signum}, shutting down gracefully...")
        simulator.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main entry point for the realistic payment simulator."""
    print("🎭 REALISTIC PAYMENT GATEWAY SIMULATOR")
    print("=" * 60)
    print("This simulator generates realistic payment traffic with:")
    print("✅ Faker-generated customer data")
    print("✅ All payment methods and card networks")
    print("✅ Regional preferences and behaviors")
    print("✅ Dynamic failure injection")
    print("✅ Business-realistic transaction patterns")
    print("✅ Comprehensive logging for LLM training")
    print("✅ Variable load patterns based on time")
    print("=" * 60)

    try:
        # Initialize simulator
        simulator = RealisticPaymentSimulator()

        # Setup signal handlers
        setup_signal_handlers(simulator)

        # Add observer for real-time monitoring
        def payment_observer(event):
            # Only log critical events to avoid spam
            if event.event_type in ["payment_final_failure", "circuit_breaker_event"]:
                timestamp = event.timestamp.strftime("%H:%M:%S")
                print(
                    f"🚨 [{timestamp}] {event.event_type}: {event.transaction.id} via {event.provider}"
                )

        simulator.gateway.monitor.add_observer(payment_observer)

        # Show initial system status
        print(f"\n🏥 Initial Provider Health:")
        health_data = simulator.gateway.get_provider_health()
        for provider, health in health_data.items():
            status = "🟢" if health["is_healthy"] else "🔴"
            print(f"   {status} {provider}: Ready")

        # Start simulation
        simulator.run_simulation()

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install required packages:")
        print("   pip install faker")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Simulator initialization error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


# Additional utility functions for analysis


class PaymentAnalyzer:
    """Utility class for analyzing simulation results."""

    @staticmethod
    def analyze_failure_patterns(log_file: str):
        """Analyze failure patterns from simulation logs."""
        import json

        try:
            with open(log_file, "r") as f:
                data = json.load(f)

            failure_logs = [
                log
                for log in data.get("logs", [])
                if log.get("event_type") == "payment_failure"
            ]

            print(f"📊 FAILURE PATTERN ANALYSIS")
            print(f"Total failures analyzed: {len(failure_logs)}")

            # Analyze by time of day
            hour_failures = {}
            for log in failure_logs:
                hour = datetime.fromisoformat(log["timestamp"]).hour
                hour_failures[hour] = hour_failures.get(hour, 0) + 1

            print(f"\n🕐 Failures by hour:")
            for hour in sorted(hour_failures.keys()):
                print(f"   {hour:02d}:00 - {hour_failures[hour]} failures")

            # Analyze by provider
            provider_failures = {}
            for log in failure_logs:
                provider = log.get("provider", "unknown")
                provider_failures[provider] = provider_failures.get(provider, 0) + 1

            print(f"\n🏦 Failures by provider:")
            for provider, count in sorted(
                provider_failures.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"   {provider}: {count} failures")

        except Exception as e:
            print(f"Analysis error: {e}")

    @staticmethod
    def generate_llm_training_prompt(stats: Dict[str, Any]) -> str:
        """Generate a sample LLM training prompt from simulation data."""

        total = stats.get("total_payments", 0)
        if total == 0:
            return "No payment data available for analysis."

        success_rate = (stats.get("successful_payments", 0) / total) * 100

        prompt = f"""
Based on the following payment gateway performance data, analyze the system health and recommend actions:

SYSTEM METRICS:
- Total Payments: {total:,}
- Success Rate: {success_rate:.1f}%
- Failed Payments: {stats.get('failed_payments', 0)}

DISTRIBUTION:
- By Network: {stats.get('by_network', {})}
- By Method: {stats.get('by_method', {})}
- By Region: {stats.get('by_region', {})}

FAILURE SCENARIOS: {len(stats.get('scenarios_triggered', []))} triggered

ANALYSIS QUESTIONS:
1. Is the {success_rate:.1f}% success rate acceptable for a payment gateway?
2. Which payment methods show the highest failure rates?
3. Are there regional patterns that suggest routing optimizations?
4. What preventive measures should be implemented?
5. Which providers should be prioritized for different transaction types?

Provide a detailed analysis with specific recommendations for improving payment success rates.
"""
        return prompt


# Example usage functions


def run_quick_test():
    """Run a quick 30-second test simulation."""
    print("🏃‍♂️ Quick Test Mode (30 seconds)")

    simulator = RealisticPaymentSimulator()
    start_time = time.time()

    while time.time() - start_time < 30:
        simulator.process_single_payment()
        time.sleep(0.5)

    simulator._print_final_stats()
start

def run_stress_test():
    """Run a high-volume stress test."""
    print("⚡ Stress Test Mode")

    simulator = RealisticPaymentSimulator()
    simulator.failure_injection_probability = 0.8  # Higher failure rate

    for i in range(200):  # Process 200 payments rapidly
        simulator.process_single_payment()
        if i % 50 == 0:
            print(f"Processed {i} payments...")
        time.sleep(0.1)  # Minimal delay

    simulator._print_final_stats()


def run_business_hours_simulation():
    """Simulate traffic patterns throughout a business day."""
    print("🏢 Business Hours Simulation")

    simulator = RealisticPaymentSimulator()

    # Simulate different hours of the day
    business_schedule = [
        (9, 20),  # 9 AM - light traffic
        (12, 100),  # Noon - lunch rush
        (15, 50),  # 3 PM - afternoon lull
        (19, 80),  # 7 PM - evening peak
        (23, 10),  # 11 PM - night traffic
    ]

    for hour, payment_count in business_schedule:
        print(f"\n⏰ Simulating {hour:02d}:00 traffic ({payment_count} payments)")

        for _ in range(payment_count):
            simulator.process_single_payment()
            time.sleep(random(0.1, 0.5))

        simulator._print_stats()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

        if mode == "quick":
            run_quick_test()
        elif mode == "stress":
            run_stress_test()
        elif mode == "business":
            run_business_hours_simulation()
        elif mode == "analyze":
            if len(sys.argv) > 2:
                PaymentAnalyzer.analyze_failure_patterns(sys.argv[2])
            else:
                print("Usage: python simulator.py analyze <log_file.json>")
        else:
            print("Available modes: quick, stress, business, analyze")
            main()
    else:
        main()
