"""Enhanced base payment provider with card network and payment method support."""

import time
import random
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ..core.models import Transaction, ProviderHealth, ProviderCapability
from ..core.enums import ErrorCode, CardNetwork, PaymentMethod, Currency, Region
from ..core.exceptions import ProviderError


class PaymentProvider(ABC):
    """Enhanced abstract base class for payment providers with network/method support."""
    
    def __init__(self, name: str, success_rate: float = 0.9, avg_latency: float = 200):
        """Initialize enhanced payment provider."""
        self.name = name
        self.success_rate = success_rate
        self.avg_latency = avg_latency
        self.request_count = 0
        self.failure_count = 0
        self.total_processing_time = 0.0
        self.is_maintenance = False
        self.rate_limit_threshold = 100
        self.rate_limit_window = 60
        self.rate_limit_counter = 0
        self.rate_limit_reset_time = datetime.now()
        
        # Network and method specific tracking
        self.network_stats = {network.value: {'requests': 0, 'failures': 0, 'total_time': 0.0} 
                             for network in CardNetwork}
        self.method_stats = {method.value: {'requests': 0, 'failures': 0, 'total_time': 0.0} 
                            for method in PaymentMethod}
        self.region_stats = {region.value: {'requests': 0, 'failures': 0, 'total_time': 0.0} 
                            for region in Region}
        
        # Provider capabilities
        self.capabilities = self.get_capabilities()
    
    @abstractmethod
    def get_specific_errors(self) -> List[ErrorCode]:
        """Get list of provider-specific error codes."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> ProviderCapability:
        """Get provider capabilities."""
        pass
    
    @abstractmethod
    def get_network_preference_score(self, network: CardNetwork) -> float:
        """Get preference score for a card network (0.0 to 1.0)."""
        pass
    
    def can_process_transaction(self, transaction: Transaction) -> bool:
        """Check if provider can process the transaction."""
        capabilities = self.capabilities
        
        # Check currency support
        if transaction.currency not in capabilities.supported_currencies:
            return False
        
        # Check amount limits
        if not (capabilities.min_amount <= transaction.amount <= capabilities.max_amount):
            return False
        
        # Check payment method
        if transaction.payment_instrument:
            if transaction.payment_instrument.method not in capabilities.supported_methods:
                return False
            
            # Check card network for card payments
            if (transaction.payment_instrument.method == PaymentMethod.CARD and 
                transaction.payment_instrument.network and
                transaction.payment_instrument.network not in capabilities.supported_networks):
                return False
        
        # Check region
        if (transaction.customer_info and 
            transaction.customer_info.region and 
            transaction.customer_info.region not in capabilities.supported_regions):
            return False
        
        return True
    
    def process_payment(self, transaction: Transaction) -> Dict[str, Any]:
        """Process a payment transaction with enhanced context."""
        start_time = time.time()
        self.request_count += 1
        
        # Track by network, method, and region
        self._track_request_start(transaction)
        
        # Check if can process
        if not self.can_process_transaction(transaction):
            processing_time = time.time() - start_time
            raise ProviderError(
                self.name,
                'Transaction not supported by provider capabilities',
                'UNSUPPORTED_TRANSACTION'
            )
        
        # Check rate limiting
        if self._is_rate_limited():
            processing_time = time.time() - start_time
            raise ProviderError(
                self.name,
                'Rate limit exceeded',
                ErrorCode.RATE_LIMITED.value
            )
        
        # Check maintenance mode
        if self.is_maintenance:
            processing_time = time.time() - start_time
            raise ProviderError(
                self.name,
                'Provider is under maintenance',
                ErrorCode.PROVIDER_MAINTENANCE.value
            )
        
        # Apply network-specific success rate adjustments
        adjusted_success_rate = self._get_adjusted_success_rate(transaction)
        
        # Simulate network latency with variations
        latency = self._calculate_processing_latency(transaction)
        time.sleep(latency)
        
        # Determine success/failure
        success = random.random() < adjusted_success_rate
        processing_time = time.time() - start_time
        self.total_processing_time += processing_time
        
        # Track completion
        self._track_request_completion(transaction, success, processing_time)
        
        if success:
            return {
                'success': True,
                'transaction_id': transaction.id,
                'provider_transaction_id': f'{self.name}_{uuid.uuid4().hex[:8]}',
                'processing_time': processing_time,
                'provider': self.name,
                'network_response_code': '00',  # Success code
                'provider_response_code': 'SUCCESS',
                'processing_fee': self._calculate_fee(transaction)
            }
        else:
            self.failure_count += 1
            error_code = self._select_contextual_error(transaction)
            
            raise ProviderError(
                self.name,
                f'Payment failed: {error_code.value}',
                error_code.value
            )
    
    def _get_adjusted_success_rate(self, transaction: Transaction) -> float:
        """Get success rate adjusted for context."""
        base_rate = self.success_rate
        
        # Network-specific adjustments
        if (transaction.payment_instrument and 
            transaction.payment_instrument.network):
            network_score = self.get_network_preference_score(transaction.payment_instrument.network)
            base_rate *= network_score
        
        # Amount-based adjustments (higher amounts slightly more likely to fail)
        if transaction.amount > 1000:
            base_rate *= 0.95
        elif transaction.amount > 5000:
            base_rate *= 0.90
        
        # Risk-based adjustments
        if transaction.customer_info and transaction.risk_score:
            if transaction.risk_score > 0.7:
                base_rate *= 0.85
            elif transaction.risk_score > 0.5:
                base_rate *= 0.95
        
        return min(base_rate, 1.0)
    
    def _calculate_processing_latency(self, transaction: Transaction) -> float:
        """Calculate processing latency based on context."""
        base_latency = self.avg_latency / 1000  # Convert to seconds
        
        # Network-specific latency variations
        if (transaction.payment_instrument and 
            transaction.payment_instrument.network):
            network_multiplier = {
                CardNetwork.VISA: 1.0,
                CardNetwork.MASTERCARD: 1.1,
                CardNetwork.AMEX: 1.3,
                CardNetwork.DISCOVER: 1.2,
                CardNetwork.JCB: 1.4,
                CardNetwork.UNIONPAY: 1.5
            }.get(transaction.payment_instrument.network, 1.0)
            base_latency *= network_multiplier
        
        # Payment method variations
        if transaction.payment_instrument:
            method_multiplier = {
                PaymentMethod.CARD: 1.0,
                PaymentMethod.DIGITAL_WALLET: 0.8,
                PaymentMethod.BANK_TRANSFER: 2.0,
                PaymentMethod.CRYPTOCURRENCY: 3.0
            }.get(transaction.payment_instrument.method, 1.0)
            base_latency *= method_multiplier
        
        # Add random variation
        variation = random.uniform(0.7, 1.3)
        return base_latency * variation
    
    def _select_contextual_error(self, transaction: Transaction) -> ErrorCode:
        """Select error code based on transaction context."""
        base_errors = self.get_specific_errors()
        
        # Network-specific errors
        if (transaction.payment_instrument and 
            transaction.payment_instrument.network):
            network = transaction.payment_instrument.network
            
            # AMEX has higher auth failure rates
            if network == CardNetwork.AMEX:
                base_errors.extend([ErrorCode.AUTHENTICATION_FAILED, 
                                  ErrorCode.BLOCKED_CARD])
            
            # International networks have region issues
            if network in [CardNetwork.JCB, CardNetwork.UNIONPAY]:
                base_errors.extend([ErrorCode.REGION_BLOCKED, 
                                  ErrorCode.CURRENCY_NOT_SUPPORTED])
        
        # Amount-based errors
        if transaction.amount > 5000:
            base_errors.extend([ErrorCode.INSUFFICIENT_FUNDS, 
                              ErrorCode.FRAUD_DETECTED])
        
        # Payment method specific errors
        if transaction.payment_instrument:
            if transaction.payment_instrument.method == PaymentMethod.DIGITAL_WALLET:
                base_errors.extend([ErrorCode.WALLET_INSUFFICIENT_BALANCE,
                                  ErrorCode.WALLET_SUSPENDED])
            elif transaction.payment_instrument.method == PaymentMethod.BANK_TRANSFER:
                base_errors.extend([ErrorCode.BANK_ACCOUNT_CLOSED,
                                  ErrorCode.BANK_TRANSFER_LIMIT_EXCEEDED])
        
        return random.choice(base_errors)
    
    def _calculate_fee(self, transaction: Transaction) -> float:
        """Calculate processing fee based on transaction details."""
        base_fee_rate = self.capabilities.processing_fee
        
        # Network-specific fees
        if (transaction.payment_instrument and 
            transaction.payment_instrument.network):
            network_fee_multiplier = {
                CardNetwork.VISA: 1.0,
                CardNetwork.MASTERCARD: 1.05,
                CardNetwork.AMEX: 1.5,
                CardNetwork.DISCOVER: 1.1,
                CardNetwork.JCB: 1.3,
                CardNetwork.UNIONPAY: 1.2
            }.get(transaction.payment_instrument.network, 1.0)
            base_fee_rate *= network_fee_multiplier
        
        return transaction.amount * (base_fee_rate / 100)
    
    def _track_request_start(self, transaction: Transaction):
        """Track request start for analytics."""
        if transaction.payment_instrument and transaction.payment_instrument.network:
            self.network_stats[transaction.payment_instrument.network.value]['requests'] += 1
        
        if transaction.payment_instrument:
            self.method_stats[transaction.payment_instrument.method.value]['requests'] += 1
        
        if transaction.customer_info and transaction.customer_info.region:
            self.region_stats[transaction.customer_info.region.value]['requests'] += 1
    
    def _track_request_completion(self, transaction: Transaction, success: bool, processing_time: float):
        """Track request completion for analytics."""
        if transaction.payment_instrument and transaction.payment_instrument.network:
            network_key = transaction.payment_instrument.network.value
            if not success:
                self.network_stats[network_key]['failures'] += 1
            self.network_stats[network_key]['total_time'] += processing_time
        
        if transaction.payment_instrument:
            method_key = transaction.payment_instrument.method.value
            if not success:
                self.method_stats[method_key]['failures'] += 1
            self.method_stats[method_key]['total_time'] += processing_time
        
        if transaction.customer_info and transaction.customer_info.region:
            region_key = transaction.customer_info.region.value
            if not success:
                self.region_stats[region_key]['failures'] += 1
            self.region_stats[region_key]['total_time'] += processing_time
    
    def _is_rate_limited(self) -> bool:
        """Check if provider is currently rate limited."""
        now = datetime.now()
        if now > self.rate_limit_reset_time:
            self.rate_limit_counter = 0
            self.rate_limit_reset_time = now + timedelta(seconds=self.rate_limit_window)
        
        if self.rate_limit_counter >= self.rate_limit_threshold:
            return True
        
        self.rate_limit_counter += 1
        return False
    
    def get_health(self) -> ProviderHealth:
        """Get enhanced health status with network/method breakdown."""
        if self.request_count == 0:
            current_success_rate = 1.0
            current_avg_latency = 0.0
        else:
            current_success_rate = (self.request_count - self.failure_count) / self.request_count
            current_avg_latency = (self.total_processing_time / self.request_count) * 1000
        
        # Calculate network-specific success rates
        network_success_rates = {}
        for network, stats in self.network_stats.items():
            if stats['requests'] > 0:
                success_rate = (stats['requests'] - stats['failures']) / stats['requests']
                network_success_rates[network] = success_rate
        
        # Calculate method-specific success rates
        method_success_rates = {}
        for method, stats in self.method_stats.items():
            if stats['requests'] > 0:
                success_rate = (stats['requests'] - stats['failures']) / stats['requests']
                method_success_rates[method] = success_rate
        
        # Calculate region-specific success rates
        region_success_rates = {}
        for region, stats in self.region_stats.items():
            if stats['requests'] > 0:
                success_rate = (stats['requests'] - stats['failures']) / stats['requests']
                region_success_rates[region] = success_rate
        
        return ProviderHealth(
            provider=self.name,
            success_rate=current_success_rate,
            avg_latency=current_avg_latency,
            current_load=self.rate_limit_counter,
            is_healthy=current_success_rate > 0.5 and not self.is_maintenance,
            last_checked=datetime.now(),
            network_success_rates=network_success_rates,
            method_success_rates=method_success_rates,
            region_success_rates=region_success_rates
        )