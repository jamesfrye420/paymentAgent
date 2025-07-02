#!/usr/bin/env python3
"""
Simple enhanced demo that works with the current system.
Tests card networks and payment methods without complex dependencies.
"""

import sys
import os
import time
import random

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from payment_gateway.gateway.payment_gateway import PaymentGateway
from payment_gateway.core.enums import RoutingStrategy


def demo_basic_enhanced_features():
    """Test basic enhanced features that work with current implementation."""
    print("="*60)
    print(" ENHANCED PAYMENT GATEWAY DEMO")
    print("="*60)
    
    gateway = PaymentGateway()
    
    # Test basic payments with different amounts and currencies
    test_scenarios = [
        {"amount": 50.0, "currency": "USD", "description": "Small USD payment"},
        {"amount": 250.0, "currency": "EUR", "description": "Medium EUR payment"},
        {"amount": 1500.0, "currency": "SGD", "description": "Large SGD payment"},
        {"amount": 25.0, "currency": "USD", "description": "Micro payment"},
        {"amount": 5000.0, "currency": "USD", "description": "High-value payment"},
    ]
    
    print("\n--- Testing Various Payment Scenarios ---")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['description']}")
        
        try:
            result = gateway.process_payment(
                amount=scenario['amount'],
                currency=scenario['currency']
            )
            
            transaction = result['transaction']
            print(f"   Amount: {scenario['currency']} {scenario['amount']}")
            print(f"   Provider: {transaction['provider']}")
            print(f"   Status: {transaction['status']}")
            print(f"   Attempts: {transaction['attempts']}")
            
            if transaction['route_history']:
                print(f"   Processing time: {transaction['route_history'][-1].get('processing_time', 'N/A'):.3f}s")
            
        except Exception as e:
            print(f"   Error: {str(e)}")
        
        time.sleep(0.5)


def demo_routing_strategies():
    """Test different routing strategies."""
    print("\n" + "="*60)
    print(" ROUTING STRATEGY COMPARISON")
    print("="*60)
    
    strategies = [
        (RoutingStrategy.HEALTH_BASED, "Health-based routing"),
        (RoutingStrategy.ROUND_ROBIN, "Round-robin routing"),
        (RoutingStrategy.FAILOVER, "Failover routing"),
    ]
    
    for strategy, description in strategies:
        print(f"\n--- {description} ---")
        
        gateway = PaymentGateway(routing_strategy=strategy)
        
        # Process several payments to see routing patterns
        providers_used = []
        for i in range(8):
            try:
                result = gateway.process_payment(
                    amount=100.0 + (i * 10),
                    currency="USD"
                )
                
                if result['success']:
                    provider = result['transaction']['provider']
                    providers_used.append(provider)
                    print(f"   Payment {i+1}: ${100 + i*10} -> {provider}")
                else:
                    print(f"   Payment {i+1}: Failed")
                    
            except Exception as e:
                print(f"   Payment {i+1}: Error - {str(e)}")
        
        # Show provider distribution
        if providers_used:
            from collections import Counter
            distribution = Counter(providers_used)
            print(f"   Provider distribution: {dict(distribution)}")
        
        time.sleep(1)


def demo_failure_scenarios():
    """Test failure scenarios and recovery."""
    print("\n" + "="*60)
    print(" FAILURE SCENARIOS & RECOVERY")
    print("="*60)
    
    gateway = PaymentGateway()
    
    failure_scenarios = [
        ("stripe_maintenance", "Stripe maintenance mode"),
        ("adyen_high_latency", "Adyen high latency"),
        ("paypal_low_success", "PayPal low success rate"),
        ("mass_failure", "System-wide failures"),
    ]
    
    for scenario_name, description in failure_scenarios:
        print(f"\n--- {description} ---")
        
        # Activate failure scenario
        result = gateway.simulate_scenario(scenario_name)
        if result['success']:
            print(f"   Scenario activated: {result['message']}")
        else:
            print(f"   Scenario failed: {result.get('error', 'Unknown error')}")
        
        # Test payments during failure
        for i in range(3):
            try:
                amount = 200.0 + (i * 50)
                result = gateway.process_payment(amount=amount, currency="USD")
                
                transaction = result['transaction']
                print(f"   Payment ${amount}: {transaction['status']} via {transaction['provider']}")
                
                # Show retry attempts
                if len(transaction['route_history']) > 1:
                    print(f"   -> Required {len(transaction['route_history'])} attempts")
                    for j, route in enumerate(transaction['route_history']):
                        print(f"      Attempt {j+1}: {route['provider']} -> {route['status']}")
                        
            except Exception as e:
                print(f"   Payment ${200 + i*50}: Error - {str(e)}")
        
        # Reset scenario
        gateway.simulate_scenario('reset_all')
        print("   Scenario reset")
        time.sleep(1)


def demo_provider_health():
    """Show provider health monitoring."""
    print("\n" + "="*60)
    print(" PROVIDER HEALTH MONITORING")
    print("="*60)
    
    gateway = PaymentGateway()
    
    # Generate some traffic to get meaningful health data
    print("\nGenerating traffic for health analysis...")
    for i in range(20):
        try:
            gateway.process_payment(
                amount=random.uniform(10, 1000),
                currency=random.choice(["USD", "EUR", "SGD"])
            )
        except:
            pass  # Ignore failures for this demo
    
    # Show provider health
    print("\n--- Provider Health Status ---")
    health_data = gateway.get_provider_health()
    
    for provider, health in health_data.items():
        print(f"\n{provider.upper()}:")
        print(f"   Success Rate: {health['success_rate']*100:.1f}%")
        print(f"   Avg Latency: {health['avg_latency']:.0f}ms")
        print(f"   Current Load: {health['current_load']}")
        print(f"   Status: {'HEALTHY' if health['is_healthy'] else 'UNHEALTHY'}")
        print(f"   Circuit Breaker: {health.get('circuit_breaker', {}).get('state', 'UNKNOWN')}")


def demo_metrics():
    """Show monitoring metrics."""
    print("\n" + "="*60)
    print(" MONITORING METRICS")
    print("="*60)
    
    gateway = PaymentGateway()
    
    # Generate mixed success/failure traffic
    print("\nGenerating test traffic...")
    
    # First, normal traffic
    for i in range(15):
        try:
            gateway.process_payment(amount=100.0, currency="USD")
        except:
            pass
    
    # Then, force some failures
    gateway.simulate_scenario('paypal_low_success')
    for i in range(10):
        try:
            gateway.process_payment(
                amount=200.0, 
                currency="USD", 
                preferred_provider="paypal"
            )
        except:
            pass
    
    # Reset and show metrics
    gateway.simulate_scenario('reset_all')
    
    print("\n--- Payment Metrics ---")
    metrics = gateway.get_metrics()
    
    if metrics:
        success_count = len(metrics.get('payment_success', []))
        failure_count = len(metrics.get('payment_failure', []))
        total_payments = success_count + failure_count
        
        if total_payments > 0:
            success_rate = (success_count / total_payments) * 100
            print(f"Total Payments: {total_payments}")
            print(f"Successful: {success_count} ({success_rate:.1f}%)")
            print(f"Failed: {failure_count} ({100-success_rate:.1f}%)")
        
        # Show recent events
        print(f"\nRecent Events:")
        for metric_type in ['payment_success', 'payment_failure']:
            if metric_type in metrics:
                count = len(metrics[metric_type])
                print(f"   {metric_type}: {count} events")
    else:
        print("No metrics available yet")


def main():
    """Run the simple enhanced demonstration."""
    print("AUTONOMOUS PAYMENT RECOVERY AGENT")
    print("Simple Enhanced Demo")
    print("="*60)
    
    try:
        # Demo 1: Basic enhanced features
        demo_basic_enhanced_features()
        
        # Demo 2: Routing strategies
        demo_routing_strategies()
        
        # Demo 3: Failure scenarios
        demo_failure_scenarios()
        
        # Demo 4: Provider health
        demo_provider_health()
        
        # Demo 5: Metrics
        demo_metrics()
        
        print("\n" + "="*60)
        print(" DEMO COMPLETE")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("✓ Multi-currency payment processing")
        print("✓ Intelligent provider routing")
        print("✓ Automatic failure recovery")
        print("✓ Circuit breaker protection")
        print("✓ Real-time health monitoring")
        print("✓ Comprehensive metrics collection")
        print("✓ Multiple routing strategies")
        
        print(f"\nSystem is ready for:")
        print("🔧 Flask API integration")
        print("🤖 LLM diagnostic brain")
        print("📊 Advanced dashboard")
        print("☁️  AWS deployment")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()