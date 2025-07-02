#!/usr/bin/env python3
"""
Enhanced demonstration with card networks, payment methods, and structured logging.

This demo showcases:
1. Card network routing (Visa vs Mastercard vs Amex etc.)
2. Payment method handling (cards, wallets, bank transfers)
3. Regional optimization
4. Structured logging for LLM training
5. Rich failure analysis with business context
"""

import sys
import os
import time
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from payment_gateway.gateway.payment_gateway import PaymentGateway
from payment_gateway.core.enums import (
    RoutingStrategy, CardNetwork, PaymentMethod, Currency, 
    Region, RiskLevel, TransactionType
)
from payment_gateway.core.models import (
    PaymentInstrument, CustomerInfo, Transaction
)
from payment_gateway.logging.structured_logger import StructuredLogger


def create_sample_customers():
    """Create diverse customer profiles for testing."""
    return [
        CustomerInfo(
            customer_id="cust_us_001",
            email="john.doe@example.com",
            country="US",
            region=Region.NORTH_AMERICA,
            risk_level=RiskLevel.LOW,
            successful_payments=45,
            preferred_providers=["stripe", "paypal"]
        ),
        CustomerInfo(
            customer_id="cust_sg_002", 
            email="alice.tan@example.sg",
            country="SG",
            region=Region.SOUTHEAST_ASIA,
            risk_level=RiskLevel.MEDIUM,
            successful_payments=12,
            previous_failures=2,
            preferred_providers=["adyen", "razorpay"]
        ),
        CustomerInfo(
            customer_id="cust_jp_003",
            email="yamada@example.jp", 
            country="JP",
            region=Region.ASIA_PACIFIC,
            risk_level=RiskLevel.LOW,
            successful_payments=78,
            preferred_providers=["adyen"]
        ),
        CustomerInfo(
            customer_id="cust_br_004",
            email="carlos@example.com.br",
            country="BR", 
            region=Region.LATIN_AMERICA,
            risk_level=RiskLevel.HIGH,
            previous_failures=5,
            successful_payments=3
        )
    ]


def create_sample_payment_instruments():
    """Create diverse payment instruments for testing."""
    return [
        # US Visa Credit Card
        PaymentInstrument(
            method=PaymentMethod.CARD,
            network=CardNetwork.VISA,
            last_four="4242",
            expiry_month=12,
            expiry_year=2025,
            country_code="US",
            issuer="Chase Bank",
            brand="visa_credit"
        ),
        # Singapore Mastercard Debit
        PaymentInstrument(
            method=PaymentMethod.CARD,
            network=CardNetwork.MASTERCARD,
            last_four="5555",
            expiry_month=8,
            expiry_year=2024,
            country_code="SG",
            issuer="DBS Bank",
            brand="mastercard_debit"
        ),
        # Japanese Amex
        PaymentInstrument(
            method=PaymentMethod.CARD,
            network=CardNetwork.AMEX,
            last_four="1005",
            expiry_month=3,
            expiry_year=2026,
            country_code="JP",
            issuer="American Express Japan",
            brand="amex_platinum"
        ),
        # Chinese UnionPay
        PaymentInstrument(
            method=PaymentMethod.CARD,
            network=CardNetwork.UNIONPAY,
            last_four="6212",
            expiry_month=6,
            expiry_year=2025,
            country_code="CN",
            issuer="Bank of China",
            brand="unionpay_credit"
        ),
        # Apple Pay Wallet
        PaymentInstrument(
            method=PaymentMethod.DIGITAL_WALLET,
            wallet_type="apple_pay",
            country_code="US"
        ),
        # Google Pay Wallet
        PaymentInstrument(
            method=PaymentMethod.DIGITAL_WALLET,
            wallet_type="google_pay",
            country_code="SG"
        )
    ]


def demo_network_routing():
    """Demonstrate intelligent routing based on card networks."""
    print("\n" + "="*80)
    print(" CARD NETWORK ROUTING DEMONSTRATION")
    print("="*80)
    
    gateway = PaymentGateway(routing_strategy=RoutingStrategy.CARD_NETWORK_OPTIMIZED)
    logger = StructuredLogger()
    
    customers = create_sample_customers()
    instruments = create_sample_payment_instruments()
    
    # Test each card network
    network_tests = [
        (CardNetwork.VISA, "US Visa Credit Card"),
        (CardNetwork.MASTERCARD, "Singapore Mastercard Debit"),
        (CardNetwork.AMEX, "Japanese American Express"),
        (CardNetwork.UNIONPAY, "Chinese UnionPay"),
    ]
    
    print("\nTesting optimal provider selection for different card networks:")
    
    for network, description in network_tests:
        print(f"\n--- Testing {description} ({network.value.upper()}) ---")
        
        # Find matching instrument
        instrument = next((i for i in instruments if i.network == network), instruments[0])
        customer = random.choice(customers)
        
        # Create transaction
        transaction_data = {
            'amount': random.uniform(50, 500),
            'currency': Currency.USD,
            'payment_instrument': instrument,
            'customer_info': customer,
            'transaction_type': TransactionType.PAYMENT
        }
        
        # Process payment
        result = gateway.process_payment(**transaction_data)
        
        transaction = result['transaction']
        print(f"Amount: ${transaction['amount']:.2f}")
        print(f"Selected Provider: {transaction['provider']}")
        print(f"Status: {transaction['status']}")
        
        # Show routing reasoning
        if transaction['route_history']:
            latest_route = transaction['route_history'][-1]
            if latest_route.get('routing_decision'):
                decision = latest_route['routing_decision']
                print(f"Routing Confidence: {decision['confidence_score']:.2f}")
                print(f"Decision Factors: {decision['decision_factors']}")
        
        # Log structured data
        if 'transaction_obj' in locals():
            logger.log_payment_event(
                payment_gateway.core.models.PaymentEvent(
                    event_type="network_routing_test",
                    transaction=transaction_obj,
                    provider=transaction['provider']
                ),
                {'test_scenario': f'{network.value}_routing_test'}
            )
        
        time.sleep(1)


def demo_payment_method_handling():
    """Demonstrate handling different payment methods."""
    print("\n" + "="*80)
    print(" PAYMENT METHOD HANDLING DEMONSTRATION")
    print("="*80)
    
    gateway = PaymentGateway()
    logger = StructuredLogger()
    
    method_tests = [
        (PaymentMethod.CARD, "Traditional Card Payment"),
        (PaymentMethod.DIGITAL_WALLET, "Digital Wallet Payment"),
        (PaymentMethod.BANK_TRANSFER, "Bank Transfer Payment"),
        (PaymentMethod.BUY_NOW_PAY_LATER, "Buy Now Pay Later"),
    ]
    
    customers = create_sample_customers()
    instruments = create_sample_payment_instruments()
    
    for method, description in method_tests:
        print(f"\n--- Testing {description} ---")
        
        # Find or create appropriate instrument
        instrument = next((i for i in instruments if i.method == method), 
                         PaymentInstrument(method=method))
        customer = random.choice(customers)
        
        try:
            result = gateway.process_payment(
                amount=random.uniform(25, 1000),
                currency=random.choice([Currency.USD, Currency.SGD, Currency.EUR]),
                payment_instrument=instrument,
                customer_info=customer
            )
            
            transaction = result['transaction']
            print(f"Method: {method.value}")
            print(f"Provider: {transaction['provider']}")
            print(f"Status: {transaction['status']}")
            print(f"Processing Fee: ${transaction['metadata'].get('processing_fee', 0):.2f}")
            
        except Exception as e:
            print(f"Method {method.value} failed: {str(e)}")
        
        time.sleep(0.5)


def demo_regional_optimization():
    """Demonstrate regional payment optimization."""
    print("\n" + "="*80)
    print(" REGIONAL PAYMENT OPTIMIZATION")
    print("="*80)
    
    gateway = PaymentGateway(routing_strategy=RoutingStrategy.HEALTH_BASED)
    logger = StructuredLogger()
    
    # Regional test scenarios
    regional_tests = [
        (Region.NORTH_AMERICA, Currency.USD, "US customer with Visa"),
        (Region.SOUTHEAST_ASIA, Currency.SGD, "Singapore customer with Mastercard"),
        (Region.ASIA_PACIFIC, Currency.USD, "Japan customer with JCB"),
        (Region.EUROPE, Currency.EUR, "European customer with Visa"),
    ]
    
    customers = create_sample_customers()
    instruments = create_sample_payment_instruments()
    
    for region, currency, description in regional_tests:
        print(f"\n--- Testing {description} ---")
        
        # Find appropriate customer and instrument
        customer = next((c for c in customers if c.region == region), customers[0])
        instrument = random.choice(instruments[:4])  # Card instruments only
        
        # Test multiple amounts to see routing patterns
        amounts = [50, 250, 1500]  # Small, medium, large
        
        for amount in amounts:
            result = gateway.process_payment(
                amount=amount,
                currency=currency,
                payment_instrument=instrument,
                customer_info=customer
            )
            
            transaction = result['transaction']
            print(f"  ${amount}: {transaction['provider']} -> {transaction['status']}")
            
            # Log regional performance
            logger.log_routing_decision(
                transaction=Transaction(**{
                    'id': transaction['id'],
                    'amount': transaction['amount'],
                    'currency': Currency(transaction['currency']),
                    'transaction_type': TransactionType.PAYMENT,
                    'provider': transaction['provider'],
                    'status': transaction['status'],
                    'payment_instrument': instrument,
                    'customer_info': customer
                }),
                decision_factors={
                    'regional_optimization': True,
                    'customer_region': region.value,
                    'provider_regional_score': 0.85,
                    'network_latency': random.uniform(100, 400)
                },
                selected_provider=transaction['provider'],
                alternatives=['alternative_provider_1', 'alternative_provider_2']
            )
        
        time.sleep(1)


def demo_failure_analysis_with_context():
    """Demonstrate rich failure analysis with business context."""
    print("\n" + "="*80)
    print(" CONTEXTUAL FAILURE ANALYSIS")
    print("="*80)
    
    gateway = PaymentGateway()
    logger = StructuredLogger()
    
    # Force various failure scenarios
    failure_scenarios = [
        ('adyen_high_latency', 'Network latency issues'),
        ('paypal_low_success', 'High failure rate scenario'),
        ('mass_failure', 'Systemic failures'),
    ]
    
    customers = create_sample_customers()
    instruments = create_sample_payment_instruments()
    
    for scenario, description in failure_scenarios:
        print(f"\n--- Analyzing: {description} ---")
        
        # Activate failure scenario
        gateway.simulate_scenario(scenario)
        
        # Process several payments to generate failure data
        for i in range(3):
            customer = random.choice(customers)
            instrument = random.choice(instruments)
            amount = random.uniform(100, 2000)
            
            result = gateway.process_payment(
                amount=amount,
                currency=Currency.USD,
                payment_instrument=instrument,
                customer_info=customer
            )
            
            transaction = result['transaction']
            
            # Analyze failure patterns
            if transaction['status'] == 'failed':
                print(f"  Failed payment: ${amount:.2f} via {transaction['provider']}")
                
                # Extract failure context
                failure_routes = [r for r in transaction['route_history'] if r['status'] == 'failed']
                for route in failure_routes:
                    print(f"    {route['provider']}: {route['reason']}")
                
                # Log structured failure analysis
                logger.log_failure_analysis(
                    transaction=Transaction(**{
                        'id': transaction['id'],
                        'amount': transaction['amount'],
                        'currency': Currency(transaction['currency']),
                        'transaction_type': TransactionType.PAYMENT,
                        'provider': transaction['provider'],
                        'status': transaction['status'],
                        'payment_instrument': instrument,
                        'customer_info': customer
                    }),
                    error_code=route.get('provider_response_code', 'UNKNOWN'),
                    error_message=route.get('reason', 'Payment failed'),
                    failure_context={
                        'scenario': scenario,
                        'network': instrument.network.value if instrument.network else None,
                        'payment_method': instrument.method.value,
                        'customer_region': customer.region.value if customer.region else None,
                        'amount_range': 'high' if amount > 1000 else 'medium' if amount > 100 else 'low',
                        'time_of_failure': datetime.now().hour,
                        'provider_response_code': route.get('provider_response_code'),
                        'processing_time': route.get('processing_time'),
                        'retry_eligible': route.get('retry_eligible', True)
                    }
                )
            else:
                print(f"  Successful payment: ${amount:.2f} via {transaction['provider']}")
        
        # Reset scenario
        gateway.simulate_scenario('reset_all')
        time.sleep(1)


def demo_structured_logging():
    """Demonstrate structured logging capabilities."""
    print("\n" + "="*80)
    print(" STRUCTURED LOGGING FOR LLM TRAINING")
    print("="*80)
    
    logger = StructuredLogger()
    
    # Generate sample log entries
    print("Generating structured logs...")
    
    # Export logs for LLM training
    log_file = logger.export_logs_for_llm_training('payment_logs_for_training.json')
    print(f"Exported logs to: {log_file}")
    
    # Generate failure patterns report
    patterns = logger.generate_failure_patterns_report()
    
    print("\nFailure Pattern Analysis:")
    print(f"Error Code Frequency: {patterns['error_code_frequency']}")
    print(f"Provider Failure Rates: {patterns['provider_failure_rates']}")
    print(f"Network-Specific Failures: {patterns['network_specific_failures']}")
    
    # Show sample log entries
    recent_logs = logger.get_logs_for_analysis(limit=5)
    
    print(f"\nSample log entries ({len(recent_logs)} recent):")
    for log in recent_logs[-3:]:  # Show last 3
        print(f"  {log['timestamp']}: {log['event_type']} - {log['message']}")
        if log.get('context'):
            print(f"    Context: {list(log['context'].keys())}")


def main():
    """Run the enhanced demonstration."""
    print("AUTONOMOUS PAYMENT RECOVERY AGENT")
    print("Enhanced Demo with Card Networks & Structured Logging")
    print("=" * 80)
    
    try:
        # Demo 1: Network-based routing
        demo_network_routing()
        
        # Demo 2: Payment method handling
        demo_payment_method_handling()
        
        # Demo 3: Regional optimization
        demo_regional_optimization()
        
        # Demo 4: Contextual failure analysis
        demo_failure_analysis_with_context()
        
        # Demo 5: Structured logging
        demo_structured_logging()
        
        print("\n" + "="*80)
        print(" ENHANCED DEMO COMPLETE")
        print("="*80)
        print("\nKey Enhanced Features Demonstrated:")
        print("✓ Card network-aware routing (Visa, Mastercard, Amex, etc.)")
        print("✓ Payment method optimization (Cards, Wallets, Bank transfers)")
        print("✓ Regional payment preferences")
        print("✓ Rich failure analysis with business context")
        print("✓ Structured logging for LLM training")
        print("✓ Provider capability matching")
        print("✓ Network-specific success rate tracking")
        print("✓ Contextual error code selection")
        
        print(f"\nLogs available in: ./logs/")
        print("Use these logs to train your LLM for payment intelligence!")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()