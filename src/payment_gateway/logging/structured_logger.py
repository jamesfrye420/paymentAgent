"""Structured logging system for payment gateway events."""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..core.models import StructuredLogEntry, Transaction, PaymentEvent
from ..core.enums import PaymentStatus, ErrorCode


class StructuredLogger:
    """
    Advanced structured logger for payment gateway events.

    Generates detailed logs optimized for LLM training and analysis.
    All logs are JSON structured with rich context for pattern recognition.
    """

    def __init__(self, log_directory: str = "logs"):
        """Initialize structured logger."""
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)

        # Create separate log files for different event types
        self.log_files = {
            "payment_events": self.log_directory / "payment_events.jsonl",
            "routing_decisions": self.log_directory / "routing_decisions.jsonl",
            "failure_analysis": self.log_directory / "failure_analysis.jsonl",
            "performance_metrics": self.log_directory / "performance_metrics.jsonl",
            "circuit_breaker_events": self.log_directory
            / "circuit_breaker_events.jsonl",
            "system_health": self.log_directory / "system_health.jsonl",
        }

        # Initialize log files
        for log_file in self.log_files.values():
            if not log_file.exists():
                log_file.touch()

    def log_payment_event(
        self, event: PaymentEvent, additional_context: Dict[str, Any] = None
    ):
        """Log a payment event with full context."""
        transaction = event.transaction
        context = additional_context or {}

        log_entry = StructuredLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level="INFO" if event.event_type.endswith("success") else "WARN",
            event_type=event.event_type,
            transaction_id=transaction.id,
            provider=event.provider,
            message=self._generate_event_message(event),
            context={
                "transaction_amount": transaction.amount,
                "transaction_currency": transaction.currency.value,
                "payment_method": (
                    transaction.payment_instrument.method.value
                    if transaction.payment_instrument
                    else None
                ),
                "card_network": (
                    transaction.payment_instrument.network.value
                    if transaction.payment_instrument
                    and transaction.payment_instrument.network
                    else None
                ),
                "customer_region": (
                    transaction.customer_info.region.value
                    if transaction.customer_info and transaction.customer_info.region
                    else None
                ),
                "customer_risk_level": (
                    transaction.customer_info.risk_level.value
                    if transaction.customer_info
                    else None
                ),
                "merchant_id": transaction.merchant_id,
                "attempt_number": transaction.attempts,
                "total_routes_tried": len(transaction.route_history),
                **context,
            },
            routing_context=self._extract_routing_context(transaction),
            performance_metrics=self._extract_performance_metrics(transaction),
            business_impact=self._calculate_business_impact(event),
        )

        self._write_log(log_entry, "payment_events")

    def log_routing_decision(
        self,
        transaction: Transaction,
        decision_factors: Dict[str, Any],
        selected_provider: str,
        alternatives: List[str],
    ):
        """Log routing decision with detailed reasoning."""
        log_entry = StructuredLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level="INFO",
            event_type="routing_decision",
            transaction_id=transaction.id,
            provider=selected_provider,
            message=f"Route selected: {selected_provider} over {alternatives}",
            context={
                "selected_provider": selected_provider,
                "alternative_providers": alternatives,
                "decision_factors": decision_factors,
                "transaction_context": {
                    "amount": transaction.amount,
                    "currency": transaction.currency.value,
                    "payment_method": (
                        transaction.payment_instrument.method.value
                        if transaction.payment_instrument
                        else None
                    ),
                    "card_network": (
                        transaction.payment_instrument.network.value
                        if transaction.payment_instrument
                        and transaction.payment_instrument.network
                        else None
                    ),
                    "customer_region": (
                        transaction.customer_info.region.value
                        if transaction.customer_info
                        and transaction.customer_info.region
                        else None
                    ),
                    "risk_score": transaction.risk_score,
                },
            },
            routing_context={
                "provider_health_scores": decision_factors.get(
                    "provider_health_scores", {}
                ),
                "network_compatibility": decision_factors.get(
                    "network_compatibility", {}
                ),
                "cost_analysis": decision_factors.get("cost_analysis", {}),
                "historical_performance": decision_factors.get(
                    "historical_performance", {}
                ),
                "regional_preferences": decision_factors.get(
                    "regional_preferences", {}
                ),
            },
        )

        self._write_log(log_entry, "routing_decisions")

    def log_failure_analysis(
        self,
        transaction: Transaction,
        error_code: str,
        error_message: str,
        failure_context: Dict[str, Any],
    ):
        """Log detailed failure analysis for pattern recognition."""
        log_entry = StructuredLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level="ERROR",
            event_type="payment_failure",
            transaction_id=transaction.id,
            provider=transaction.provider,
            message=f"Payment failed: {error_message}",
            context={
                "error_code": error_code,
                "error_message": error_message,
                "failure_context": failure_context,
                "payment_context": {
                    "amount": transaction.amount,
                    "currency": transaction.currency.value,
                    "payment_method": (
                        transaction.payment_instrument.method.value
                        if transaction.payment_instrument
                        else None
                    ),
                    "card_network": (
                        transaction.payment_instrument.network.value
                        if transaction.payment_instrument
                        and transaction.payment_instrument.network
                        else None
                    ),
                    "issuer": (
                        transaction.payment_instrument.issuer
                        if transaction.payment_instrument
                        else None
                    ),
                    "country": (
                        transaction.payment_instrument.country_code
                        if transaction.payment_instrument
                        else None
                    ),
                },
                "attempt_history": [
                    route.to_dict() for route in transaction.route_history
                ],
                "time_of_day": datetime.now().hour,
                "day_of_week": datetime.now().weekday(),
            },
            error_details={
                "provider_response_code": failure_context.get("provider_response_code"),
                "provider_message": failure_context.get("provider_message"),
                "network_response_code": failure_context.get("network_response_code"),
                "processing_time": failure_context.get("processing_time"),
                "retry_eligible": failure_context.get("retry_eligible", True),
                "similar_failures_count": failure_context.get(
                    "similar_failures_count", 0
                ),
            },
        )

        self._write_log(log_entry, "failure_analysis")

    def log_circuit_breaker_event(
        self,
        provider: str,
        state_change: str,
        failure_count: int,
        context: Dict[str, Any],
    ):
        """Log circuit breaker state changes."""
        log_entry = StructuredLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level="WARN",
            event_type="circuit_breaker_event",
            provider=provider,
            message=f"Circuit breaker {state_change} for {provider}",
            context={
                "state_change": state_change,
                "failure_count": failure_count,
                "provider_context": context,
                "impact_assessment": {
                    "affected_transactions": context.get("pending_transactions", 0),
                    "alternative_providers": context.get("alternative_providers", []),
                    "expected_recovery_time": context.get("recovery_time_estimate"),
                },
            },
        )

        self._write_log(log_entry, "circuit_breaker_events")

    def log_performance_metrics(self, provider: str, metrics: Dict[str, float]):
        """Log performance metrics for trend analysis."""
        log_entry = StructuredLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level="INFO",
            event_type="performance_metrics",
            provider=provider,
            message=f"Performance metrics for {provider}",
            metrics=metrics,
            performance_metrics={
                "success_rate": metrics.get("success_rate", 0),
                "avg_latency": metrics.get("avg_latency", 0),
                "throughput": metrics.get("throughput", 0),
                "error_rate": metrics.get("error_rate", 0),
                "network_breakdown": metrics.get("network_breakdown", {}),
                "method_breakdown": metrics.get("method_breakdown", {}),
                "regional_breakdown": metrics.get("regional_breakdown", {}),
            },
        )

        self._write_log(log_entry, "performance_metrics")

    def log_system_health(self, overall_health: Dict[str, Any]):
        """Log overall system health status."""
        log_entry = StructuredLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level="INFO",
            event_type="system_health",
            message="System health check",
            context=overall_health,
            metrics={
                "total_success_rate": overall_health.get("total_success_rate", 0),
                "avg_processing_time": overall_health.get("avg_processing_time", 0),
                "active_providers": overall_health.get("active_providers", 0),
                "circuit_breakers_open": overall_health.get("circuit_breakers_open", 0),
            },
        )

        self._write_log(log_entry, "system_health")

    def _generate_event_message(self, event: PaymentEvent) -> str:
        """Generate human-readable message for the event."""
        transaction = event.transaction

        messages = {
            "payment_initiated": f"Payment initiated: ${transaction.amount} {transaction.currency.value} via {event.provider}",
            "payment_success": f"Payment successful: ${transaction.amount} {transaction.currency.value} via {event.provider}",
            "payment_failure": f"Payment failed: ${transaction.amount} {transaction.currency.value} via {event.provider}",
            "payment_retry": f"Payment retry attempt {transaction.attempts}: ${transaction.amount} via {event.provider}",
            "payment_final_failure": f"Payment permanently failed after {transaction.attempts} attempts: ${transaction.amount}",
            "routing_switch": f"Payment rerouted from {event.metadata.get('previous_provider', 'unknown')} to {event.provider}",
        }

        return messages.get(event.event_type, f"Payment event: {event.event_type}")

    def _extract_routing_context(self, transaction: Transaction) -> Dict[str, Any]:
        """Extract routing context from transaction."""
        if not transaction.route_history:
            return {}

        latest_route = transaction.route_history[-1]
        return {
            "current_provider": transaction.provider,
            "providers_tried": list(
                set(route.provider for route in transaction.route_history)
            ),
            "routing_decisions": [
                route.routing_decision.to_dict() if route.routing_decision else None
                for route in transaction.route_history
            ],
            "provider_switches": len(
                set(route.provider for route in transaction.route_history)
            )
            - 1,
        }

    def _extract_performance_metrics(
        self, transaction: Transaction
    ) -> Dict[str, float]:
        """Extract performance metrics from transaction."""
        if not transaction.route_history:
            return {}

        processing_times = [
            route.processing_time
            for route in transaction.route_history
            if route.processing_time is not None
        ]

        return {
            "total_processing_time": sum(processing_times) if processing_times else 0,
            "avg_processing_time": (
                sum(processing_times) / len(processing_times) if processing_times else 0
            ),
            "max_processing_time": max(processing_times) if processing_times else 0,
            "attempts_count": len(transaction.route_history),
            "successful_attempts": len(
                [r for r in transaction.route_history if r.status == "success"]
            ),
            "failed_attempts": len(
                [r for r in transaction.route_history if r.status == "failed"]
            ),
        }

    def _calculate_business_impact(self, event: PaymentEvent) -> Dict[str, Any]:
        """Calculate business impact of the event."""
        transaction = event.transaction

        impact = {
            "revenue_at_risk": (
                transaction.amount if event.event_type.endswith("failure") else 0
            ),
            "customer_experience_score": self._calculate_cx_score(transaction),
            "provider_reputation_impact": self._calculate_reputation_impact(event),
            "cost_implications": {
                "processing_fees": transaction.metadata.get("processing_fee", 0),
                "retry_costs": len(transaction.route_history)
                * 0.01,  # Estimated retry cost
                "opportunity_cost": (
                    transaction.amount * 0.1
                    if event.event_type.endswith("failure")
                    else 0
                ),
            },
        }

        return impact

    def _calculate_cx_score(self, transaction: Transaction) -> float:
        """Calculate customer experience score based on transaction journey."""
        base_score = 100.0

        # Deduct points for each retry
        retry_penalty = (transaction.attempts - 1) * 10

        # Deduct points for long processing time
        total_time = sum(
            route.processing_time
            for route in transaction.route_history
            if route.processing_time is not None
        )
        time_penalty = min(total_time * 5, 30)  # Max 30 points penalty

        # Deduct points for failure
        failure_penalty = 50 if transaction.status == PaymentStatus.FAILED else 0

        return max(0, base_score - retry_penalty - time_penalty - failure_penalty)

    def _calculate_reputation_impact(self, event: PaymentEvent) -> Dict[str, float]:
        """Calculate provider reputation impact."""
        if event.event_type.endswith("success"):
            return {"reputation_score": 1.0, "trust_impact": 0.1}
        elif event.event_type.endswith("failure"):
            return {"reputation_score": -1.0, "trust_impact": -0.2}
        else:
            return {"reputation_score": 0.0, "trust_impact": 0.0}

    def _write_log(self, log_entry: StructuredLogEntry, log_type: str):
        """Write log entry to appropriate file."""
        log_file = self.log_files.get(log_type)
        if not log_file:
            return

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                json.dump(log_entry.to_dict(), f, ensure_ascii=False)
                f.write("\n")
        except Exception as e:
            print(f"Failed to write log entry: {e}")

    def get_logs_for_analysis(
        self, log_type: str = None, since: datetime = None, limit: int = None
    ) -> List[Dict[str, Any]]:
        """Retrieve logs for analysis."""
        logs = []

        log_files_to_read = (
            [self.log_files[log_type]] if log_type else self.log_files.values()
        )

        for log_file in log_files_to_read:
            if not log_file.exists():
                continue

            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            log_data = json.loads(line.strip())

                            # Filter by timestamp if specified
                            if since:
                                log_time = datetime.fromisoformat(log_data["timestamp"])
                                if log_time < since:
                                    continue

                            logs.append(log_data)

                            # Apply limit if specified
                            if limit and len(logs) >= limit:
                                return logs[-limit:]

            except Exception as e:
                print(f"Failed to read log file {log_file}: {e}")

        return logs

    def export_logs_for_llm_training(
        self, output_file: str, include_patterns: List[str] = None
    ) -> str:
        """Export logs in format optimized for LLM training."""
        all_logs = self.get_logs_for_analysis()

        # Filter logs if patterns specified
        if include_patterns:
            filtered_logs = []
            for log in all_logs:
                if any(
                    pattern in log.get("event_type", "") for pattern in include_patterns
                ):
                    filtered_logs.append(log)
            all_logs = filtered_logs

        # Create training dataset format
        training_data = {
            "dataset_info": {
                "name": "payment_gateway_logs",
                "version": "1.0",
                "description": "Structured logs from autonomous payment recovery agent",
                "total_entries": len(all_logs),
                "export_timestamp": datetime.now().isoformat(),
                "log_types": list(set(log.get("event_type", "") for log in all_logs)),
            },
            "logs": all_logs,
        }

        output_path = Path(output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def generate_failure_patterns_report(self) -> Dict[str, Any]:
        """Generate a report of failure patterns for LLM analysis."""
        failure_logs = self.get_logs_for_analysis("failure_analysis")

        patterns = {
            "error_code_frequency": {},
            "provider_failure_rates": {},
            "network_specific_failures": {},
            "time_based_patterns": {},
            "amount_based_patterns": {},
        }

        for log in failure_logs:
            error_code = log.get("context", {}).get("error_code", "UNKNOWN")
            provider = log.get("provider", "UNKNOWN")

            # Error code frequency
            patterns["error_code_frequency"][error_code] = (
                patterns["error_code_frequency"].get(error_code, 0) + 1
            )

            # Provider failure rates
            patterns["provider_failure_rates"][provider] = (
                patterns["provider_failure_rates"].get(provider, 0) + 1
            )

            # Network specific failures
            network = (
                log.get("context", {}).get("payment_context", {}).get("card_network")
            )
            if network:
                if network not in patterns["network_specific_failures"]:
                    patterns["network_specific_failures"][network] = {}
                patterns["network_specific_failures"][network][error_code] = (
                    patterns["network_specific_failures"][network].get(error_code, 0)
                    + 1
                )

            # Time-based patterns
            hour = datetime.fromisoformat(log["timestamp"]).hour
            patterns["time_based_patterns"][hour] = (
                patterns["time_based_patterns"].get(hour, 0) + 1
            )

            # Amount-based patterns
            amount = log.get("context", {}).get("payment_context", {}).get("amount", 0)
            amount_range = f"{int(amount//100)*100}-{int(amount//100)*100+99}"
            patterns["amount_based_patterns"][amount_range] = (
                patterns["amount_based_patterns"].get(amount_range, 0) + 1
            )

        return patterns
