"""
Failure injection patterns for realistic payment simulation.
"""

import random
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from ..core.config import FAILURE_SCENARIOS


@dataclass
class FailureScenario:
    """Represents a failure scenario with its characteristics."""
    name: str
    description: str
    probability: float
    duration_range: tuple  # (min_seconds, max_seconds)
    severity: str  # 'low', 'medium', 'high', 'critical'
    affected_providers: List[str]
    trigger_conditions: Dict[str, Any]
    recovery_time_range: tuple  # (min_seconds, max_seconds)


class FailureInjector:
    """Manages realistic failure injection patterns for payment simulation."""
    
    def __init__(self, gateway=None):
        """Initialize failure injector."""
        self.gateway = gateway
        self.active_scenarios = {}
        self.scenario_history = []
        self.base_failure_probability = 0.05  # 5% base chance
        
        # Define realistic failure scenarios
        self.scenarios = self._define_failure_scenarios()
        
        # Failure pattern weights by time
        self.time_based_weights = self._define_time_patterns()
        
        # Recovery timers
        self.recovery_timers = {}
        
        # Cascade failure tracking
        self.cascade_triggers = {}
    
    def _define_failure_scenarios(self) -> Dict[str, FailureScenario]:
        """Define realistic failure scenarios based on real-world patterns."""
        scenarios = {
            'provider_maintenance': FailureScenario(
                name='provider_maintenance',
                description='Scheduled maintenance window',
                probability=0.02,
                duration_range=(300, 1800),  # 5-30 minutes
                severity='medium',
                affected_providers=['stripe', 'adyen', 'paypal', 'razorpay'],
                trigger_conditions={'time_range': [(2, 6), (23, 24)]},  # Late night/early morning
                recovery_time_range=(60, 300)
            ),
            
            'network_latency_spike': FailureScenario(
                name='network_latency_spike',
                description='Network infrastructure issues causing high latency',
                probability=0.08,
                duration_range=(120, 600),  # 2-10 minutes
                severity='medium',
                affected_providers=['adyen', 'stripe'],
                trigger_conditions={'traffic_multiplier': 1.5},  # During high traffic
                recovery_time_range=(30, 120)
            ),
            
            'rate_limiting': FailureScenario(
                name='rate_limiting',
                description='Provider rate limits exceeded',
                probability=0.06,
                duration_range=(60, 300),  # 1-5 minutes
                severity='low',
                affected_providers=['razorpay', 'paypal'],
                trigger_conditions={'volume_spike': True},
                recovery_time_range=(60, 180)
            ),
            
            'payment_processor_outage': FailureScenario(
                name='payment_processor_outage',
                description='Complete payment processor failure',
                probability=0.01,
                duration_range=(180, 900),  # 3-15 minutes
                severity='critical',
                affected_providers=['stripe', 'adyen', 'paypal', 'razorpay'],
                trigger_conditions={},
                recovery_time_range=(300, 600)
            ),
            
            'fraud_detection_overload': FailureScenario(
                name='fraud_detection_overload',
                description='Fraud detection system causing delays',
                probability=0.04,
                duration_range=(180, 480),  # 3-8 minutes
                severity='medium',
                affected_providers=['stripe', 'adyen'],
                trigger_conditions={'high_risk_volume': True},
                recovery_time_range=(120, 300)
            ),
            
            'database_connection_issues': FailureScenario(
                name='database_connection_issues',
                description='Database connectivity problems',
                probability=0.03,
                duration_range=(60, 240),  # 1-4 minutes
                severity='high',
                affected_providers=['all'],
                trigger_conditions={},
                recovery_time_range=(30, 120)
            ),
            
            'regional_network_partition': FailureScenario(
                name='regional_network_partition',
                description='Regional network connectivity issues',
                probability=0.015,
                duration_range=(300, 1200),  # 5-20 minutes
                severity='high',
                affected_providers=['region_specific'],
                trigger_conditions={'region': ['SOUTHEAST_ASIA', 'ASIA_PACIFIC']},
                recovery_time_range=(180, 600)
            ),
            
            'api_version_deprecation': FailureScenario(
                name='api_version_deprecation',
                description='Legacy API version causing failures',
                probability=0.025,
                duration_range=(600, 3600),  # 10-60 minutes
                severity='medium',
                affected_providers=['paypal', 'razorpay'],
                trigger_conditions={},
                recovery_time_range=(300, 900)
            ),
            
            'ssl_certificate_expiry': FailureScenario(
                name='ssl_certificate_expiry',
                description='SSL certificate expiration causing connection failures',
                probability=0.005,
                duration_range=(1800, 7200),  # 30 minutes - 2 hours
                severity='critical',
                affected_providers=['random_single'],
                trigger_conditions={},
                recovery_time_range=(900, 1800)
            ),
            
            'load_balancer_failure': FailureScenario(
                name='load_balancer_failure',
                description='Load balancer issues causing intermittent failures',
                probability=0.02,
                duration_range=(240, 720),  # 4-12 minutes
                severity='high',
                affected_providers=['stripe', 'adyen'],
                trigger_conditions={'peak_hours': True},
                recovery_time_range=(120, 360)
            )
        }
        
        return scenarios
    
    def _define_time_patterns(self) -> Dict[int, float]:
        """Define failure probability weights by hour of day."""
        # Higher failure probability during peak hours and deployment windows
        return {
            0: 0.3,   # Late night - lower activity but maintenance windows
            1: 0.2,   # Very late night
            2: 0.5,   # Common maintenance window
            3: 0.4,   # Maintenance window
            4: 0.3,   # Pre-dawn
            5: 0.4,   # Early morning
            6: 0.6,   # Morning commute start
            7: 1.2,   # Peak morning traffic
            8: 1.5,   # Business hours start
            9: 1.3,   # High business activity
            10: 1.1,  # Normal business
            11: 1.2,  # Pre-lunch peak
            12: 1.8,  # Lunch peak - highest load
            13: 1.6,  # Lunch continues
            14: 1.0,  # Afternoon lull
            15: 1.1,  # Afternoon pickup
            16: 1.2,  # Late afternoon
            17: 1.4,  # End of business day
            18: 1.7,  # Evening commute peak
            19: 1.9,  # Evening peak - dinner/shopping
            20: 1.5,  # Evening activity
            21: 1.2,  # Evening wind down
            22: 0.8,  # Night activity
            23: 0.5   # Late night
        }
    
    def should_inject_failure(self, context: Dict[str, Any] = None) -> bool:
        """Determine if a failure should be injected based on context."""
        if context is None:
            context = {}
        
        # Base probability adjusted by time patterns
        current_hour = datetime.now().hour
        time_weight = self.time_based_weights.get(current_hour, 1.0)
        
        adjusted_probability = self.base_failure_probability * time_weight
        
        # Adjust based on current traffic
        traffic_mult = context.get('traffic_multiplier', 1.0)
        if traffic_mult > 1.5:  # High traffic increases failure chance
            adjusted_probability *= 1.3
        elif traffic_mult < 0.5:  # Low traffic decreases failure chance
            adjusted_probability *= 0.7
        
        # Reduce probability if recent failures occurred
        recent_failures = len([s for s in self.scenario_history 
                             if (datetime.now() - s['timestamp']).seconds < 300])
        if recent_failures > 0:
            adjusted_probability *= (0.5 ** recent_failures)
        
        return random.random() < adjusted_probability
    
    def select_failure_scenario(self, context: Dict[str, Any] = None) -> Optional[FailureScenario]:
        """Select an appropriate failure scenario based on context."""
        if context is None:
            context = {}
        
        current_hour = datetime.now().hour
        available_scenarios = []
        
        for scenario in self.scenarios.values():
            # Check if scenario conditions are met
            conditions_met = True
            
            # Time-based conditions
            if 'time_range' in scenario.trigger_conditions:
                time_ranges = scenario.trigger_conditions['time_range']
                in_time_range = any(start <= current_hour <= end for start, end in time_ranges)
                if not in_time_range:
                    conditions_met = False
            
            # Traffic-based conditions
            if 'traffic_multiplier' in scenario.trigger_conditions:
                required_traffic = scenario.trigger_conditions['traffic_multiplier']
                actual_traffic = context.get('traffic_multiplier', 1.0)
                if actual_traffic < required_traffic:
                    conditions_met = False
            
            # Peak hours condition
            if scenario.trigger_conditions.get('peak_hours'):
                is_peak = context.get('is_peak_hour', False)
                if not is_peak:
                    conditions_met = False
            
            # Volume spike condition
            if scenario.trigger_conditions.get('volume_spike'):
                has_spike = context.get('volume_spike', False)
                if not has_spike:
                    conditions_met = False
            
            # High risk volume condition
            if scenario.trigger_conditions.get('high_risk_volume'):
                high_risk = context.get('high_risk_transactions', 0) > 5
                if not high_risk:
                    conditions_met = False
            
            # Regional conditions
            if 'region' in scenario.trigger_conditions:
                required_regions = scenario.trigger_conditions['region']
                current_region = context.get('region')
                if current_region not in required_regions:
                    conditions_met = False
            
            if conditions_met:
                available_scenarios.append(scenario)
        
        if not available_scenarios:
            # Fallback to basic scenarios
            available_scenarios = [
                self.scenarios['network_latency_spike'],
                self.scenarios['rate_limiting']
            ]
        
        # Weight by probability
        weights = [s.probability for s in available_scenarios]
        return random.choices(available_scenarios, weights=weights)[0]
    
    def inject_failure(self, scenario: FailureScenario, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Inject a specific failure scenario."""
        if not self.gateway:
            return {'success': False, 'error': 'No gateway configured'}
        
        scenario_id = f"{scenario.name}_{datetime.now().strftime('%H%M%S')}"
        
        # Determine affected providers
        affected_providers = self._select_affected_providers(scenario, context)
        
        # Calculate duration
        duration = random(*scenario.duration_range)
        
        # Record scenario start
        scenario_record = {
            'id': scenario_id,
            'scenario': scenario,
            'affected_providers': affected_providers,
            'timestamp': datetime.now(),
            'duration': duration,
            'context': context or {},
            'status': 'active'
        }
        
        self.active_scenarios[scenario_id] = scenario_record
        self.scenario_history.append(scenario_record)
        
        # Apply failure to gateway
        result = self._apply_failure_to_gateway(scenario, affected_providers)
        
        # Schedule recovery
        self._schedule_recovery(scenario_id, duration)
        
        # Check for cascade failures
        self._check_cascade_triggers(scenario, affected_providers)
        
        return {
            'success': True,
            'scenario_id': scenario_id,
            'scenario_name': scenario.name,
            'description': scenario.description,
            'affected_providers': affected_providers,
            'duration': duration,
            'severity': scenario.severity
        }
    
    def _select_affected_providers(self, scenario: FailureScenario, 
                                 context: Dict[str, Any] = None) -> List[str]:
        """Select which providers are affected by the scenario."""
        if scenario.affected_providers == ['all']:
            return ['stripe', 'adyen', 'paypal', 'razorpay']
        elif scenario.affected_providers == ['random_single']:
            return [random.choice(['stripe', 'adyen', 'paypal', 'razorpay'])]
        elif scenario.affected_providers == ['region_specific']:
            # Select providers based on region
            region = context.get('region', 'SOUTHEAST_ASIA') if context else 'SOUTHEAST_ASIA'
            region_providers = {
                'NORTH_AMERICA': ['stripe', 'paypal'],
                'EUROPE': ['adyen', 'stripe'],
                'SOUTHEAST_ASIA': ['razorpay', 'adyen'],
                'ASIA_PACIFIC': ['adyen', 'stripe'],
                'LATIN_AMERICA': ['stripe', 'paypal']
            }
            return region_providers.get(region, ['stripe', 'adyen'])
        else:
            # Random selection from specified providers
            num_affected = random.randint(1, len(scenario.affected_providers))
            return random.sample(scenario.affected_providers, num_affected)
    
    def _apply_failure_to_gateway(self, scenario: FailureScenario, 
                                 affected_providers: List[str]) -> Dict[str, Any]:
        """Apply the failure scenario to the gateway."""
        results = {}
        
        for provider in affected_providers:
            if scenario.name == 'provider_maintenance':
                result = self.gateway.simulate_scenario(f'{provider}_maintenance')
            elif scenario.name == 'network_latency_spike':
                result = self.gateway.simulate_scenario(f'{provider}_high_latency')
            elif scenario.name == 'rate_limiting':
                result = self.gateway.simulate_scenario(f'{provider}_rate_limit')
            elif scenario.name == 'payment_processor_outage':
                result = self.gateway.simulate_scenario(f'{provider}_low_success')
            elif scenario.name in ['fraud_detection_overload', 'database_connection_issues']:
                result = self.gateway.simulate_scenario(f'{provider}_low_success')
            else:
                # Generic failure simulation
                result = self.gateway.simulate_scenario(f'{provider}_low_success')
            
            results[provider] = result
        
        return results
    
    def _schedule_recovery(self, scenario_id: str, duration: float):
        """Schedule automatic recovery from failure scenario."""
        def recover():
            if scenario_id in self.active_scenarios:
                scenario_record = self.active_scenarios[scenario_id]
                scenario_record['status'] = 'recovering'
                
                # Apply recovery
                self._recover_from_scenario(scenario_record)
                
                # Mark as completed
                scenario_record['status'] = 'completed'
                scenario_record['end_time'] = datetime.now()
                
                # Remove from active scenarios
                del self.active_scenarios[scenario_id]
        
        timer = threading.Timer(duration, recover)
        timer.start()
        self.recovery_timers[scenario_id] = timer
    
    def _recover_from_scenario(self, scenario_record: Dict[str, Any]):
        """Recover from a failure scenario."""
        scenario = scenario_record['scenario']
        recovery_time = random(*scenario.recovery_time_range)
        
        # Gradual recovery for more realistic behavior
        if recovery_time > 60:  # For longer recoveries, do gradual restoration
            self._gradual_recovery(scenario_record, recovery_time)
        else:
            # Immediate recovery
            self.gateway.simulate_scenario('reset_all')
    
    def _gradual_recovery(self, scenario_record: Dict[str, Any], total_recovery_time: float):
        """Implement gradual recovery for more realistic behavior."""
        affected_providers = scenario_record['affected_providers']
        steps = 3  # Recovery in 3 steps
        step_duration = total_recovery_time / steps
        
        def recovery_step(step_num):
            if step_num < steps:
                # Partial recovery - improve but don't fully restore
                recovery_percentage = (step_num + 1) / steps
                
                for provider in affected_providers:
                    # Gradually improve success rate
                    current_rate = 0.3 + (0.6 * recovery_percentage)  # 30% -> 90%
                    self.gateway.configure_provider(provider, success_rate=current_rate)
                
                # Schedule next step
                timer = threading.Timer(step_duration, lambda: recovery_step(step_num + 1))
                timer.start()
            else:
                # Full recovery
                self.gateway.simulate_scenario('reset_all')
        
        # Start gradual recovery
        recovery_step(0)
    
    def _check_cascade_triggers(self, scenario: FailureScenario, affected_providers: List[str]):
        """Check if this failure should trigger cascade failures."""
        if scenario.severity in ['high', 'critical'] and len(affected_providers) >= 2:
            # High severity failures affecting multiple providers can cause cascades
            cascade_probability = 0.3 if scenario.severity == 'high' else 0.5
            
            if random.random() < cascade_probability:
                # Trigger cascade failure after a delay
                delay = random(30, 120)  # 30 seconds to 2 minutes
                
                def trigger_cascade():
                    cascade_scenario = self._generate_cascade_scenario(scenario, affected_providers)
                    if cascade_scenario:
                        self.inject_failure(cascade_scenario)
                
                timer = threading.Timer(delay, trigger_cascade)
                timer.start()
    
    def _generate_cascade_scenario(self, original_scenario: FailureScenario, 
                                 original_providers: List[str]) -> Optional[FailureScenario]:
        """Generate a cascade failure scenario."""
        # Cascade failures typically affect different components
        cascade_scenarios = {
            'database_overload': FailureScenario(
                name='cascade_database_overload',
                description=f'Database overload caused by {original_scenario.name}',
                probability=1.0,  # Guaranteed since it's triggered
                duration_range=(60, 300),
                severity='medium',
                affected_providers=['all'],
                trigger_conditions={},
                recovery_time_range=(30, 120)
            ),
            'network_congestion': FailureScenario(
                name='cascade_network_congestion',
                description=f'Network congestion from rerouted traffic due to {original_scenario.name}',
                probability=1.0,
                duration_range=(120, 480),
                severity='medium',
                affected_providers=[p for p in ['stripe', 'adyen', 'paypal', 'razorpay'] 
                                  if p not in original_providers],
                trigger_conditions={},
                recovery_time_range=(60, 180)
            )
        }
        
        cascade_type = random.choice(list(cascade_scenarios.keys()))
        return cascade_scenarios[cascade_type]
    
    def get_active_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active failure scenarios."""
        return self.active_scenarios.copy()
    
    def get_scenario_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get failure scenario history for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [s for s in self.scenario_history if s['timestamp'] > cutoff_time]
    
    def force_recovery(self, scenario_id: str = None):
        """Force recovery from specific scenario or all active scenarios."""
        if scenario_id:
            if scenario_id in self.active_scenarios:
                # Cancel recovery timer
                if scenario_id in self.recovery_timers:
                    self.recovery_timers[scenario_id].cancel()
                    del self.recovery_timers[scenario_id]
                
                # Apply immediate recovery
                scenario_record = self.active_scenarios[scenario_id]
                self._recover_from_scenario(scenario_record)
                
                # Clean up
                scenario_record['status'] = 'force_recovered'
                scenario_record['end_time'] = datetime.now()
                del self.active_scenarios[scenario_id]
        else:
            # Force recovery from all active scenarios
            for scenario_id in list(self.active_scenarios.keys()):
                self.force_recovery(scenario_id)
    
    def get_failure_probability_factors(self, context: Dict[str, Any] = None) -> Dict[str, float]:
        """Get factors affecting current failure probability."""
        if context is None:
            context = {}
        
        current_hour = datetime.now().hour
        time_weight = self.time_based_weights.get(current_hour, 1.0)
        
        traffic_mult = context.get('traffic_multiplier', 1.0)
        traffic_factor = 1.3 if traffic_mult > 1.5 else 0.7 if traffic_mult < 0.5 else 1.0
        
        recent_failures = len([s for s in self.scenario_history 
                             if (datetime.now() - s['timestamp']).seconds < 300])
        recent_failure_factor = 0.5 ** recent_failures if recent_failures > 0 else 1.0
        
        return {
            'base_probability': self.base_failure_probability,
            'time_weight': time_weight,
            'traffic_factor': traffic_factor,
            'recent_failure_factor': recent_failure_factor,
            'final_probability': self.base_failure_probability * time_weight * traffic_factor * recent_failure_factor
        }
    
    def simulate_specific_scenario(self, scenario_name: str, 
                                 context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simulate a specific named scenario for testing."""
        if scenario_name not in self.scenarios:
            return {'success': False, 'error': f'Unknown scenario: {scenario_name}'}
        
        scenario = self.scenarios[scenario_name]
        return self.inject_failure(scenario, context)
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """Get statistics about failure patterns."""
        if not self.scenario_history:
            return {'total_scenarios': 0}
        
        # Count by scenario type
        scenario_counts = {}
        severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        provider_impact = {}
        
        for record in self.scenario_history:
            scenario_name = record['scenario'].name
            scenario_counts[scenario_name] = scenario_counts.get(scenario_name, 0) + 1
            
            severity = record['scenario'].severity
            severity_counts[severity] += 1
            
            for provider in record['affected_providers']:
                provider_impact[provider] = provider_impact.get(provider, 0) + 1
        
        # Calculate average duration
        durations = [record['duration'] for record in self.scenario_history]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_scenarios': len(self.scenario_history),
            'scenario_counts': scenario_counts,
            'severity_distribution': severity_counts,
            'provider_impact': provider_impact,
            'average_duration_seconds': avg_duration,
            'active_scenarios': len(self.active_scenarios)
        }
    
    def export_failure_log(self, filename: str = None) -> str:
        """Export failure scenario log for analysis."""
        import json
        from datetime import datetime
        
        if filename is None:
            filename = f"failure_scenarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_scenarios': len(self.scenario_history),
            'active_scenarios_count': len(self.active_scenarios),
            'scenarios': []
        }
        
        for record in self.scenario_history:
            scenario_data = {
                'id': record['id'],
                'name': record['scenario'].name,
                'description': record['scenario'].description,
                'severity': record['scenario'].severity,
                'affected_providers': record['affected_providers'],
                'start_time': record['timestamp'].isoformat(),
                'duration': record['duration'],
                'status': record['status'],
                'context': record['context']
            }
            
            if 'end_time' in record:
                scenario_data['end_time'] = record['end_time'].isoformat()
            
            export_data['scenarios'].append(scenario_data)
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return filename