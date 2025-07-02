"""Main payment gateway orchestrator."""

import uuid
import time
from datetime import datetime
from typing import Dict, Optional, Any

from ..core.models import Transaction, PaymentInstrument, CustomerInfo ,PaymentEvent, Route, RetryConfig, CircuitBreakerConfig
from ..core.enums import PaymentStatus, RoutingStrategy, TransactionType
from ..core.exceptions import (
    TransactionNotFoundError,
    InvalidProviderError,
    ProviderError,
    CircuitBreakerError
)
from ..providers.base import PaymentProvider
from ..providers.stripe_provider import StripeProvider
from ..providers.adyen_provider import AdyenProvider
from ..providers.paypal_provider import PayPalProvider
from ..providers.razorpay_provider import RazorpayProvider
from ..monitoring.monitor import PaymentMonitor
from ..monitoring.circuit_breaker import CircuitBreaker


class PaymentGateway:
    """
    Main payment gateway orchestrator with self-healing capabilities.
    
    Manages payment processing across multiple providers with intelligent
    routing, failure detection, and automatic recovery mechanisms.
    """
    
    def __init__(self, routing_strategy: RoutingStrategy = RoutingStrategy.HEALTH_BASED):
        """
        Initialize payment gateway.
        
        Args:
            routing_strategy: Strategy for selecting payment providers
        """
        # Initialize providers
        self.providers = {
            'stripe': StripeProvider(),
            'adyen': AdyenProvider(),
            'paypal': PayPalProvider(),
            'razorpay': RazorpayProvider()
        }
        
        # Initialize circuit breakers for each provider
        circuit_config = CircuitBreakerConfig()
        self.circuit_breakers = {
            name: CircuitBreaker(circuit_config) 
            for name in self.providers.keys()
        }
        
        # Transaction storage
        self.transactions: Dict[str, Transaction] = {}
        
        # Configuration
        self.routing_strategy = routing_strategy
        self.retry_config = RetryConfig()
        
        # Monitoring
        self.monitor = PaymentMonitor()
        self.monitor.start_monitoring()
        
        # Round robin counter for round robin routing
        self._round_robin_counter = 0
    
    def process_payment(
        self, 
        amount: float, 
        currency = 'USD', 
        preferred_provider: Optional[str] = None,
        customer_id: Optional[str] = None,
        payment_instrument: Optional[PaymentInstrument] = None,
        customer_info: Optional[CustomerInfo] = None,
        transaction_type: Optional[TransactionType] = None, 
        merchant_id: Optional[str] = None,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a payment transaction.
        
        Args:
            amount: Payment amount
            currency: Payment currency (str or Currency enum)
            preferred_provider: Preferred payment provider
            customer_id: Optional customer identifier (for backward compatibility)
            payment_instrument: PaymentInstrument object with card/payment details
            customer_info: CustomerInfo object with customer context
            transaction_type: Type of transaction (default: PAYMENT)
            merchant_id: Merchant identifier
            order_id: Order identifier
            
        Returns:
            Payment processing result
        """
        from ..core.enums import Currency, TransactionType
        from ..core.models import PaymentInstrument, CustomerInfo
        
        transaction_id = str(uuid.uuid4())
        
        # Handle currency conversion (backward compatibility)
        if isinstance(currency, str):
            try:
                currency_enum = Currency(currency.upper())
            except ValueError:
                currency_enum = Currency.USD
        else:
            currency_enum = currency
        
        # Handle transaction type
        if transaction_type is None:
            from ..core.enums import TransactionType
            transaction_type = TransactionType.PAYMENT
        
        # Create customer info from customer_id if needed (backward compatibility)
        if customer_info is None and customer_id:
            from ..core.models import CustomerInfo
            from ..core.enums import RiskLevel
            customer_info = CustomerInfo(
                customer_id=customer_id,
                risk_level=RiskLevel.LOW
            )
        
        # Create transaction first (without provider)
        transaction = Transaction(
            id=transaction_id,
            amount=amount,
            currency=currency_enum,
            transaction_type=transaction_type,
            provider="temp",  # Temporary, will be updated
            status=PaymentStatus.PENDING,
            payment_instrument=payment_instrument,
            customer_info=customer_info,
            merchant_id=merchant_id,
            order_id=order_id
        )
        
        # Legacy customer_id support
        if customer_id and not customer_info:
            transaction.metadata['customer_id'] = customer_id
        
        # Select provider based on transaction context
        if preferred_provider:
            if preferred_provider not in self.providers:
                raise InvalidProviderError(preferred_provider)
            provider_name = preferred_provider
        else:
            provider_name = self._select_optimal_provider(transaction)
        
        # Update transaction with selected provider
        transaction.provider = provider_name
        
        self.transactions[transaction_id] = transaction
        
        # Emit event
        self.monitor.emit_event(
            PaymentEvent("payment_initiated", transaction, provider_name)
        )
        
        return self._attempt_payment(transaction)
    
    def _select_optimal_provider(self, transaction: Optional[Transaction] = None) -> str:
        """Select the optimal payment provider based on routing strategy and transaction context."""
        if self.routing_strategy == RoutingStrategy.HEALTH_BASED:
            return self._select_healthiest_provider(transaction)
        elif self.routing_strategy == RoutingStrategy.ROUND_ROBIN:
            return self._select_round_robin(transaction)
        elif self.routing_strategy == RoutingStrategy.FAILOVER:
            return self._select_failover(transaction)
        elif self.routing_strategy == RoutingStrategy.CARD_NETWORK_OPTIMIZED:
            return self._select_network_optimized(transaction)
        elif self.routing_strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._select_cost_optimized(transaction)
        else:
            return 'stripe'  # default fallback
    
    def _select_network_optimized(self, transaction: Optional[Transaction] = None) -> str:
        """Select provider optimized for the card network."""
        if not transaction or not transaction.payment_instrument or not transaction.payment_instrument.network:
            return self._select_healthiest_provider(transaction)
        
        network = transaction.payment_instrument.network
        best_provider = None
        best_score = -1
        
        for name, provider in self.providers.items():
            # Check if provider can handle the transaction
            if hasattr(provider, 'can_process_transaction') and not provider.can_process_transaction(transaction):
                continue
                
            health = provider.get_health()
            circuit_state = self.circuit_breakers[name].get_state()
            
            if health.is_healthy and circuit_state.value != 'OPEN':
                # Get network preference score
                network_score = 1.0
                if hasattr(provider, 'get_network_preference_score'):
                    network_score = provider.get_network_preference_score(network)
                
                # Combine health and network preference
                combined_score = health.success_rate * network_score
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_provider = name
        
        return best_provider or 'stripe'
    
    def _select_cost_optimized(self, transaction: Optional[Transaction] = None) -> str:
        """Select provider with lowest processing costs."""
        if not transaction:
            return self._select_healthiest_provider(transaction)
        
        best_provider = None
        lowest_cost = float('inf')
        
        for name, provider in self.providers.items():
            # Check if provider can handle the transaction
            if hasattr(provider, 'can_process_transaction') and not provider.can_process_transaction(transaction):
                continue
                
            health = provider.get_health()
            circuit_state = self.circuit_breakers[name].get_state()
            
            if health.is_healthy and circuit_state.value != 'OPEN':
                # Calculate estimated cost
                if hasattr(provider, 'capabilities'):
                    fee_rate = provider.capabilities.processing_fee
                    estimated_cost = transaction.amount * (fee_rate / 100)
                    
                    if estimated_cost < lowest_cost:
                        lowest_cost = estimated_cost
                        best_provider = name
        
        return best_provider or 'stripe'
    
    def _select_healthiest_provider(self, transaction: Optional[Transaction] = None) -> str:
        """Select provider based on health metrics and transaction compatibility."""
        best_provider = None
        best_score = -1
        
        for name, provider in self.providers.items():
            # Check if provider can handle the transaction
            if transaction and hasattr(provider, 'can_process_transaction') and not provider.can_process_transaction(transaction):
                continue
                
            health = provider.get_health()
            circuit_state = self.circuit_breakers[name].get_state()
            
            if health.is_healthy and circuit_state.value != 'OPEN':
                # Score based on success rate and inverse of latency
                score = health.success_rate * (1000 / max(health.avg_latency, 1))
                if score > best_score:
                    best_score = score
                    best_provider = name
        
        return best_provider or 'stripe'  # fallback
    
    def _select_round_robin(self, transaction: Optional[Transaction] = None) -> str:
        """Select provider using round-robin strategy."""
        provider_names = list(self.providers.keys())
        
        # Filter by transaction compatibility if transaction provided
        if transaction:
            compatible_providers = []
            for name in provider_names:
                provider = self.providers[name]
                if hasattr(provider, 'can_process_transaction') and provider.can_process_transaction(transaction):
                    compatible_providers.append(name)
            
            if compatible_providers:
                provider_names = compatible_providers
        
        self._round_robin_counter = (self._round_robin_counter + 1) % len(provider_names)
        return provider_names[self._round_robin_counter]
    
    def _select_failover(self, transaction: Optional[Transaction] = None) -> str:
        """Select provider using failover strategy."""
        preference_order = ['stripe', 'adyen', 'paypal', 'razorpay']
        
        for provider_name in preference_order:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                
                # Check transaction compatibility
                if transaction and hasattr(provider, 'can_process_transaction') and not provider.can_process_transaction(transaction):
                    continue
                    
                health = provider.get_health()
                circuit_state = self.circuit_breakers[provider_name].get_state()
                
                if health.is_healthy and circuit_state.value != 'OPEN':
                    return provider_name
        
        return 'stripe'  # ultimate fallback
    
    def _attempt_payment(self, transaction: Transaction) -> Dict[str, Any]:
        """Attempt payment processing with retry logic."""
        for attempt in range(self.retry_config.max_attempts):
            transaction.attempts = attempt + 1
            
            try:
                # Get provider and circuit breaker
                provider = self.providers[transaction.provider]
                circuit_breaker = self.circuit_breakers[transaction.provider]
                
                # Attempt payment through circuit breaker
                result = circuit_breaker.call(provider.process_payment, transaction)
                
                # Record successful route
                route = Route(
                    provider=transaction.provider,
                    attempt_number=attempt + 1,
                    status='success',
                    timestamp=datetime.now(),
                    processing_time=result.get('processing_time')
                )
                transaction.route_history.append(route)
                
                # Update transaction
                transaction.status = PaymentStatus.SUCCESS
                transaction.metadata.update(result)
                
                # Emit success event and record metrics
                self.monitor.emit_event(
                    PaymentEvent("payment_success", transaction, transaction.provider)
                )
                self.monitor.record_metric("payment_success", 1, {'provider': transaction.provider})
                self.monitor.record_metric("payment_latency", result.get('processing_time', 0))
                
                return {
                    'success': True,
                    'transaction': transaction.to_dict()
                }
                
            except (ProviderError, CircuitBreakerError) as e:
                # Record failed route
                route = Route(
                    provider=transaction.provider,
                    attempt_number=attempt + 1,
                    status='failed',
                    timestamp=datetime.now(),
                    reason=str(e)
                )
                transaction.route_history.append(route)
                
                # Emit failure event and record metrics
                self.monitor.emit_event(
                    PaymentEvent("payment_failure", transaction, transaction.provider, {'error': str(e)})
                )
                self.monitor.record_metric("payment_failure", 1, {'provider': transaction.provider})
                
                # Try different provider for next attempt
                if attempt < self.retry_config.max_attempts - 1:
                    self._switch_provider(transaction)
                    delay = self.retry_config.get_delay(attempt + 1)
                    time.sleep(delay)
                    continue
                
            except Exception as e:
                # Unexpected error
                route = Route(
                    provider=transaction.provider,
                    attempt_number=attempt + 1,
                    status='error',
                    timestamp=datetime.now(),
                    reason=f"Unexpected error: {str(e)}"
                )
                transaction.route_history.append(route)
                
                if attempt < self.retry_config.max_attempts - 1:
                    self._switch_provider(transaction)
                    delay = self.retry_config.get_delay(attempt + 1)
                    time.sleep(delay)
                    continue
        
        # All attempts failed
        transaction.status = PaymentStatus.FAILED
        self.monitor.emit_event(
            PaymentEvent("payment_final_failure", transaction, transaction.provider)
        )
        
        return {
            'success': False,
            'transaction': transaction.to_dict(),
            'error': 'Payment failed after all retry attempts'
        }
    
    def _switch_provider(self, transaction: Transaction):
        """Switch to a different provider for retry."""
        current_provider = transaction.provider
        available_providers = [
            name for name in self.providers.keys() 
            if name != current_provider
        ]
        
        if available_providers:
            # Create a temporary transaction copy for provider selection
            temp_transaction = Transaction(
                id=transaction.id,
                amount=transaction.amount,
                currency=transaction.currency,
                transaction_type=transaction.transaction_type,
                provider="temp",
                status=transaction.status,
                payment_instrument=transaction.payment_instrument,
                customer_info=transaction.customer_info
            )
            
            # Select best available provider using current routing strategy
            original_providers = self.providers
            temp_providers = {
                k: v for k, v in self.providers.items() 
                if k != current_provider
            }
            self.providers = temp_providers
            
            try:
                new_provider = self._select_optimal_provider(temp_transaction)
                transaction.provider = new_provider
            finally:
                self.providers = original_providers
    
    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get status of a specific transaction.
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            Transaction status dictionary
            
        Raises:
            TransactionNotFoundError: If transaction doesn't exist
        """
        if transaction_id not in self.transactions:
            raise TransactionNotFoundError(transaction_id)
        
        return self.transactions[transaction_id].to_dict()
    
    def retry_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Retry a failed payment.
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            Retry result
            
        Raises:
            TransactionNotFoundError: If transaction doesn't exist
        """
        if transaction_id not in self.transactions:
            raise TransactionNotFoundError(transaction_id)
        
        transaction = self.transactions[transaction_id]
        
        if transaction.status == PaymentStatus.SUCCESS:
            return {
                'success': False, 
                'error': 'Transaction already successful'
            }
        
        # Reset transaction for retry
        transaction.status = PaymentStatus.RETRYING
        transaction.provider = self._select_optimal_provider()
        
        return self._attempt_payment(transaction)
    
    def get_provider_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all providers."""
        health_data = {}
        
        for name, provider in self.providers.items():
            health = provider.get_health()
            circuit_stats = self.circuit_breakers[name].get_stats()
            
            health_data[name] = health.to_dict()
            health_data[name]['circuit_breaker'] = circuit_stats
        
        return health_data
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get monitoring metrics."""
        return self.monitor.get_metrics()
    
    def configure_provider(self, provider_name: str, **config):
        """
        Configure provider settings.
        
        Args:
            provider_name: Provider to configure
            **config: Configuration parameters
            
        Raises:
            InvalidProviderError: If provider doesn't exist
        """
        if provider_name not in self.providers:
            raise InvalidProviderError(provider_name)
        
        self.providers[provider_name].configure(**config)
    
    def simulate_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """
        Trigger predefined failure scenarios for testing.
        
        Args:
            scenario_name: Name of scenario to activate
            
        Returns:
            Result of scenario activation
        """
        scenarios = {
            'stripe_maintenance': lambda: self.configure_provider('stripe', is_maintenance=True),
            'adyen_high_latency': lambda: self.configure_provider('adyen', avg_latency=2000),
            'paypal_low_success': lambda: self.configure_provider('paypal', success_rate=0.3),
            'razorpay_rate_limit': lambda: self.configure_provider('razorpay', rate_limit_threshold=1),
            'mass_failure': lambda: [
                self.configure_provider(p, success_rate=0.1) 
                for p in self.providers.keys()
            ],
            'circuit_breaker_test': self._activate_circuit_breaker_test,
            'reset_all': self._reset_all_providers
        }
        
        if scenario_name in scenarios:
            try:
                result = scenarios[scenario_name]()
                if isinstance(result, str):
                    message = result
                elif isinstance(result, list):
                    message = f'Scenario {scenario_name} activated (bulk operation)'
                else:
                    message = f'Scenario {scenario_name} activated'
                    
                return {
                    'success': True, 
                    'message': message
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to activate scenario {scenario_name}: {str(e)}'
                }
        else:
            return {
                'success': False, 
                'error': f'Unknown scenario: {scenario_name}'
            }
    
    def _activate_circuit_breaker_test(self):
        """Activate circuit breaker test scenario."""
        self.circuit_breakers['stripe'].force_open()
        return "Circuit breaker for Stripe forced to OPEN state"
    
    def _reset_all_providers(self):
        """Reset all providers to normal state."""
        for provider_name in self.providers.keys():
            self.configure_provider(
                provider_name, 
                success_rate=0.9, 
                avg_latency=200, 
                is_maintenance=False,
                rate_limit_threshold=100
            )
        for cb in self.circuit_breakers.values():
            cb.force_close()
        return "All providers reset to normal state"
    
    def set_routing_strategy(self, strategy: RoutingStrategy):
        """Set the routing strategy for provider selection."""
        self.routing_strategy = strategy
    
    def __del__(self):
        """Cleanup when gateway is destroyed."""
        if hasattr(self, 'monitor'):
            self.monitor.stop_monitoring()