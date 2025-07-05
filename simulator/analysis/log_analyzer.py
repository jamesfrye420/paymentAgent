import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import logging
from pathlib import Path
import re
from enum import Enum
from dateutil import parser as date_parser


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    FAILURE_PATTERNS = "failure_patterns"
    PROVIDER_PERFORMANCE = "provider_performance"
    RISK_ANALYSIS = "risk_analysis"
    ROUTING_EFFICIENCY = "routing_efficiency"
    FRAUD_DETECTION = "fraud_detection"
    TEMPORAL_PATTERNS = "temporal_patterns"


@dataclass
class PaymentTransaction:
    """Structured representation of a payment transaction"""

    transaction_id: str
    amount: float
    currency: str
    provider: str
    status: str
    success: bool
    timestamp: datetime
    customer_id: str
    risk_level: str
    region: str
    payment_method: str
    network: str
    failure_reason: Optional[str] = None
    processing_time: Optional[float] = None
    network_latency: Optional[float] = None
    provider_health: Optional[float] = None
    retry_count: int = 0
    circuit_breaker_state: Optional[str] = None


@dataclass
class PatternAnalysisResult:
    """Result structure for pattern analysis"""

    pattern_type: str
    confidence: float
    description: str
    metrics: Dict[str, Any]
    recommendations: List[str]
    risk_score: float


class PaymentLogsProcessor:
    """Main processor for payment logs analysis"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.transactions: List[PaymentTransaction] = []
        self.analysis_cache: Dict[str, Any] = {}
        self.patterns_db: Dict[str, PatternAnalysisResult] = {}

    def load_jsonl_file(self, file_path: str) -> List[Dict]:
        """Load and parse JSONL file"""
        try:
            with open(file_path, "r") as f:
                data = []
                for line_num, line in enumerate(f, 1):
                    try:
                        if line.strip():
                            data.append(json.loads(line.strip()))
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing line {line_num}: {e}")
                        continue
                return data
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            return []

    def parse_transaction(self, raw_data: Dict) -> PaymentTransaction:
        """Parse raw transaction data into structured format"""
        transaction = raw_data.get("transaction", {})
        customer_info = transaction.get("customer_info", {})
        route_history = raw_data.get("route_history", {})
        payment_instrument = transaction.get("payment_instrument", {})
        metadata = raw_data.get("metadata", {})

        return PaymentTransaction(
            transaction_id=raw_data.get("transaction_id", ""),
            amount=transaction.get("amount", 0.0),
            currency=transaction.get("currency", ""),
            provider=transaction.get("provider", ""),
            status=transaction.get("status", ""),
            success=raw_data.get("success", False),
            timestamp=self._safe_parse_timestamp(raw_data.get("timestamp")),
            customer_id=customer_info.get("customer_id", ""),
            risk_level=customer_info.get("risk_level", "unknown"),
            region=customer_info.get("region", ""),
            payment_method=payment_instrument.get("method", ""),
            network=payment_instrument.get("network", ""),
            failure_reason=route_history.get("reason"),
            processing_time=metadata.get("processing_time"),
            network_latency=route_history.get("network_latency"),
            provider_health=route_history.get("routing_decision", {})
            .get("decision_factors", {})
            .get("provider_health"),
            circuit_breaker_state=route_history.get("routing_decision", {})
            .get("decision_factors", {})
            .get("circuit_breaker_state"),
        )

    def _safe_parse_timestamp(self, timestamp_str: str) -> datetime:
        """Safely parse timestamp string to datetime object"""
        try:
            if isinstance(timestamp_str, str):
                # Handle ISO format with Z
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str.replace("Z", "+00:00")
                return date_parser.parse(timestamp_str)
            elif isinstance(timestamp_str, datetime):
                return timestamp_str
            else:
                return datetime.now()
        except Exception:
            return datetime.now()

    def process_data(self, file_path: str) -> None:
        """Process payment logs data"""
        logger.info(f"Processing payment logs from: {file_path}")

        raw_data = self.load_jsonl_file(file_path)
        if not raw_data:
            logger.error("No data loaded")
            return

        # Parse transactions
        self.transactions = []
        for raw_transaction in raw_data:
            try:
                transaction = self.parse_transaction(raw_transaction)
                self.transactions.append(transaction)
            except Exception as e:
                logger.error(f"Error parsing transaction: {e}")
                continue

        logger.info(f"Processed {len(self.transactions)} transactions")

    def extract_failure_patterns(self) -> PatternAnalysisResult:
        """Extract and analyze failure patterns"""
        failed_transactions = [t for t in self.transactions if not t.success]

        if not failed_transactions:
            return PatternAnalysisResult(
                pattern_type="failure_patterns",
                confidence=0.0,
                description="No failed transactions found",
                metrics={},
                recommendations=[],
                risk_score=0.0,
            )

        # Analyze failure reasons
        failure_reasons = Counter(
            [t.failure_reason for t in failed_transactions if t.failure_reason]
        )

        # Provider failure rates
        provider_failures = defaultdict(list)
        for t in failed_transactions:
            provider_failures[t.provider].append(t)

        provider_failure_rates = {}
        for provider, failures in provider_failures.items():
            total_provider_txns = len(
                [t for t in self.transactions if t.provider == provider]
            )
            failure_rate = (
                len(failures) / total_provider_txns if total_provider_txns > 0 else 0
            )
            provider_failure_rates[provider] = failure_rate

        # Risk level correlation
        risk_failure_correlation = {}
        for risk_level in ["low", "medium", "high"]:
            risk_transactions = [
                t for t in self.transactions if t.risk_level == risk_level
            ]
            risk_failures = [t for t in risk_transactions if not t.success]
            if risk_transactions:
                risk_failure_correlation[risk_level] = len(risk_failures) / len(
                    risk_transactions
                )

        # Circuit breaker analysis
        circuit_breaker_issues = len(
            [t for t in failed_transactions if t.circuit_breaker_state == "OPEN"]
        )

        # Generate recommendations
        recommendations = []

        # Top failure reason recommendations
        if failure_reasons:
            top_failure = failure_reasons.most_common(1)[0]
            recommendations.append(
                f"Address top failure reason: {top_failure[0]} ({top_failure[1]} occurrences)"
            )

        # Provider-specific recommendations
        worst_provider = (
            max(provider_failure_rates.items(), key=lambda x: x[1])
            if provider_failure_rates
            else None
        )
        if worst_provider and worst_provider[1] > 0.1:
            recommendations.append(
                f"Review {worst_provider[0]} provider configuration (failure rate: {worst_provider[1]:.2%})"
            )

        # Risk-based recommendations
        if risk_failure_correlation.get("high", 0) > 0.3:
            recommendations.append(
                "Implement additional verification for high-risk customers"
            )

        if circuit_breaker_issues > 0:
            recommendations.append(
                f"Review circuit breaker configuration ({circuit_breaker_issues} failed transactions)"
            )

        # Calculate confidence and risk score
        total_failures = len(failed_transactions)
        confidence = min(1.0, total_failures / 100)  # Higher confidence with more data
        risk_score = total_failures / len(self.transactions) if self.transactions else 0

        return PatternAnalysisResult(
            pattern_type="failure_patterns",
            confidence=confidence,
            description=f"Analyzed {total_failures} failed transactions out of {len(self.transactions)} total",
            metrics={
                "total_failures": total_failures,
                "failure_rate": risk_score,
                "top_failure_reasons": dict(failure_reasons.most_common(5)),
                "provider_failure_rates": provider_failure_rates,
                "risk_level_correlation": risk_failure_correlation,
                "circuit_breaker_issues": circuit_breaker_issues,
            },
            recommendations=recommendations,
            risk_score=risk_score,
        )

    def analyze_provider_performance(self) -> PatternAnalysisResult:
        """Analyze provider performance metrics"""
        provider_metrics = defaultdict(
            lambda: {
                "total_transactions": 0,
                "successful_transactions": 0,
                "failed_transactions": 0,
                "total_amount": 0.0,
                "processing_times": [],
                "network_latencies": [],
                "health_scores": [],
            }
        )

        for t in self.transactions:
            metrics = provider_metrics[t.provider]
            metrics["total_transactions"] += 1
            metrics["total_amount"] += t.amount

            if t.success:
                metrics["successful_transactions"] += 1
            else:
                metrics["failed_transactions"] += 1

            if t.processing_time:
                metrics["processing_times"].append(t.processing_time)
            if t.network_latency:
                metrics["network_latencies"].append(t.network_latency)
            if t.provider_health:
                metrics["health_scores"].append(t.provider_health)

        # Calculate performance scores
        provider_scores = {}
        for provider, metrics in provider_metrics.items():
            success_rate = (
                metrics["successful_transactions"] / metrics["total_transactions"]
            )
            avg_processing_time = (
                np.mean(metrics["processing_times"])
                if metrics["processing_times"]
                else 0
            )
            avg_latency = (
                np.mean(metrics["network_latencies"])
                if metrics["network_latencies"]
                else 0
            )
            avg_health = (
                np.mean(metrics["health_scores"]) if metrics["health_scores"] else 0
            )

            # Composite score (higher is better)
            performance_score = (
                (success_rate * 0.4)
                + (avg_health * 0.3)
                + (1 / (1 + avg_processing_time) * 0.3)
            )

            provider_scores[provider] = {
                "success_rate": success_rate,
                "avg_processing_time": avg_processing_time,
                "avg_latency": avg_latency,
                "avg_health": avg_health,
                "performance_score": performance_score,
                "total_volume": metrics["total_transactions"],
                "total_amount": metrics["total_amount"],
            }

        # Generate recommendations
        recommendations = []

        # Best and worst performers
        if provider_scores:
            best_provider = max(
                provider_scores.items(), key=lambda x: x[1]["performance_score"]
            )
            worst_provider = min(
                provider_scores.items(), key=lambda x: x[1]["performance_score"]
            )

            recommendations.append(
                f"Best performing provider: {best_provider[0]} (score: {best_provider[1]['performance_score']:.3f})"
            )
            recommendations.append(
                f"Consider routing more traffic to {best_provider[0]}"
            )

            if worst_provider[1]["performance_score"] < 0.7:
                recommendations.append(
                    f"Review {worst_provider[0]} provider issues (score: {worst_provider[1]['performance_score']:.3f})"
                )

        # Latency recommendations
        high_latency_providers = [
            p for p, s in provider_scores.items() if s["avg_latency"] > 500
        ]
        if high_latency_providers:
            recommendations.append(
                f"High latency providers need attention: {', '.join(high_latency_providers)}"
            )

        return PatternAnalysisResult(
            pattern_type="provider_performance",
            confidence=0.9,
            description=f"Analyzed performance of {len(provider_scores)} providers",
            metrics=provider_scores,
            recommendations=recommendations,
            risk_score=(
                1
                - (
                    sum(s["performance_score"] for s in provider_scores.values())
                    / len(provider_scores)
                )
                if provider_scores
                else 0
            ),
        )

    def detect_fraud_patterns(self) -> PatternAnalysisResult:
        """Detect potential fraud patterns"""
        fraud_indicators = []

        # Analyze by customer
        customer_analysis = defaultdict(
            lambda: {
                "transactions": [],
                "total_amount": 0.0,
                "success_rate": 0.0,
                "currencies": set(),
                "regions": set(),
                "time_span": None,
            }
        )

        for t in self.transactions:
            customer_analysis[t.customer_id]["transactions"].append(t)
            customer_analysis[t.customer_id]["total_amount"] += t.amount
            customer_analysis[t.customer_id]["currencies"].add(t.currency)
            customer_analysis[t.customer_id]["regions"].add(t.region)

        # Calculate customer metrics
        for customer_id, data in customer_analysis.items():
            transactions = data["transactions"]
            successful = sum(1 for t in transactions if t.success)
            data["success_rate"] = successful / len(transactions)

            # Time span analysis
            timestamps = [t.timestamp for t in transactions]
            if len(timestamps) > 1:
                data["time_span"] = max(timestamps) - min(timestamps)

        # Detect anomalies
        suspicious_customers = []

        for customer_id, data in customer_analysis.items():
            risk_score = 0
            reasons = []

            # Multiple currencies
            if len(data["currencies"]) > 2:
                risk_score += 0.3
                reasons.append("Multiple currencies")

            # Multiple regions
            if len(data["regions"]) > 1:
                risk_score += 0.4
                reasons.append("Multiple regions")

            # Low success rate with high volume
            if data["success_rate"] < 0.3 and len(data["transactions"]) > 5:
                risk_score += 0.5
                reasons.append("Low success rate with high volume")

            # Rapid transactions
            if (
                data["time_span"]
                and data["time_span"] < timedelta(hours=1)
                and len(data["transactions"]) > 10
            ):
                risk_score += 0.6
                reasons.append("Rapid transaction pattern")

            if risk_score > 0.5:
                suspicious_customers.append(
                    {
                        "customer_id": customer_id,
                        "risk_score": risk_score,
                        "reasons": reasons,
                        "transaction_count": len(data["transactions"]),
                        "total_amount": data["total_amount"],
                    }
                )

        # Sort by risk score
        suspicious_customers.sort(key=lambda x: x["risk_score"], reverse=True)

        # Generate recommendations
        recommendations = []
        if suspicious_customers:
            recommendations.append(
                f"Review {len(suspicious_customers)} suspicious customers"
            )
            recommendations.append(
                "Implement additional KYC verification for multi-region transactions"
            )
            recommendations.append("Set up alerts for rapid transaction patterns")

        return PatternAnalysisResult(
            pattern_type="fraud_detection",
            confidence=0.8,
            description=f"Analyzed {len(customer_analysis)} unique customers",
            metrics={
                "suspicious_customers": suspicious_customers[:10],  # Top 10
                "total_customers_analyzed": len(customer_analysis),
                "fraud_indicators_found": len(suspicious_customers),
            },
            recommendations=recommendations,
            risk_score=(
                len(suspicious_customers) / len(customer_analysis)
                if customer_analysis
                else 0
            ),
        )

    def analyze_temporal_patterns(self) -> PatternAnalysisResult:
        """Analyze temporal patterns in transactions"""
        if not self.transactions:
            return PatternAnalysisResult(
                pattern_type="temporal_patterns",
                confidence=0.0,
                description="No transactions to analyze",
                metrics={},
                recommendations=[],
                risk_score=0.0,
            )

        # Hour-based analysis
        hourly_stats = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0})
        daily_stats = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0})

        for t in self.transactions:
            hour = t.timestamp.hour
            day = t.timestamp.strftime("%Y-%m-%d")

            hourly_stats[hour]["total"] += 1
            daily_stats[day]["total"] += 1

            if t.success:
                hourly_stats[hour]["success"] += 1
                daily_stats[day]["success"] += 1
            else:
                hourly_stats[hour]["failed"] += 1
                daily_stats[day]["failed"] += 1

        # Find peak hours
        peak_hour = max(hourly_stats.items(), key=lambda x: x[1]["total"])
        worst_hour = min(
            hourly_stats.items(),
            key=lambda x: x[1]["success"] / x[1]["total"] if x[1]["total"] > 0 else 1,
        )

        # Daily trends
        daily_success_rates = {
            day: stats["success"] / stats["total"]
            for day, stats in daily_stats.items()
            if stats["total"] > 0
        }

        recommendations = []
        recommendations.append(
            f"Peak hour: {peak_hour[0]}:00 ({peak_hour[1]['total']} transactions)"
        )
        recommendations.append(
            f"Lowest success rate hour: {worst_hour[0]}:00 ({worst_hour[1]['success']}/{worst_hour[1]['total']} success rate)"
        )

        if daily_success_rates:
            avg_success_rate = sum(daily_success_rates.values()) / len(
                daily_success_rates
            )
            recommendations.append(
                f"Average daily success rate: {avg_success_rate:.2%}"
            )

        return PatternAnalysisResult(
            pattern_type="temporal_patterns",
            confidence=0.9,
            description=f"Analyzed temporal patterns across {len(daily_stats)} days",
            metrics={
                "hourly_stats": dict(hourly_stats),
                "daily_stats": dict(daily_stats),
                "peak_hour": peak_hour[0],
                "worst_hour": worst_hour[0],
                "daily_success_rates": daily_success_rates,
            },
            recommendations=recommendations,
            risk_score=(
                1 - (sum(daily_success_rates.values()) / len(daily_success_rates))
                if daily_success_rates
                else 0
            ),
        )

    def run_comprehensive_analysis(
        self, file_path: str
    ) -> Dict[str, PatternAnalysisResult]:
        """Run comprehensive analysis on payment logs"""
        logger.info("Starting comprehensive payment logs analysis")

        # Process data
        self.process_data(file_path)

        if not self.transactions:
            logger.error("No transactions processed")
            return {}

        # Run all analyses
        analyses = {}

        try:
            analyses["failure_patterns"] = self.extract_failure_patterns()
            logger.info("Completed failure patterns analysis")
        except Exception as e:
            logger.error(f"Error in failure patterns analysis: {e}")

        try:
            analyses["provider_performance"] = self.analyze_provider_performance()
            logger.info("Completed provider performance analysis")
        except Exception as e:
            logger.error(f"Error in provider performance analysis: {e}")

        try:
            analyses["fraud_detection"] = self.detect_fraud_patterns()
            logger.info("Completed fraud detection analysis")
        except Exception as e:
            logger.error(f"Error in fraud detection analysis: {e}")

        try:
            analyses["temporal_patterns"] = self.analyze_temporal_patterns()
            logger.info("Completed temporal patterns analysis")
        except Exception as e:
            logger.error(f"Error in temporal patterns analysis: {e}")

        return analyses

    def generate_summary_report(
        self, analyses: Dict[str, PatternAnalysisResult]
    ) -> str:
        """Generate a comprehensive summary report"""
        report = []
        report.append("=" * 60)
        report.append("PAYMENT LOGS ANALYSIS SUMMARY REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Transactions Analyzed: {len(self.transactions)}")
        report.append("")

        for analysis_type, result in analyses.items():
            report.append(f"\n{analysis_type.upper().replace('_', ' ')}")
            report.append("-" * 40)
            report.append(f"Confidence: {result.confidence:.2%}")
            report.append(f"Risk Score: {result.risk_score:.2%}")
            report.append(f"Description: {result.description}")
            report.append("")

            if result.recommendations:
                report.append("Recommendations:")
                for i, rec in enumerate(result.recommendations, 1):
                    report.append(f"  {i}. {rec}")
            report.append("")

        return "\n".join(report)


# Example usage and testing
def main():
    """Main function to demonstrate usage"""

    # Initialize processor
    processor = PaymentLogsProcessor()

    # Run comprehensive analysis
    file_path = "realistic_payment_result_logs_20250705_205148.jsonl"
    analyses = processor.run_comprehensive_analysis(file_path)

    # Generate and print summary report
    summary_report = processor.generate_summary_report(analyses)
    print(summary_report)

    # Save detailed results to JSON
    detailed_results = {
        analysis_type: {
            "pattern_type": result.pattern_type,
            "confidence": result.confidence,
            "description": result.description,
            "metrics": result.metrics,
            "recommendations": result.recommendations,
            "risk_score": result.risk_score,
        }
        for analysis_type, result in analyses.items()
    }

    with open(
        f"payment_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w"
    ) as f:
        json.dump(detailed_results, f, indent=2, default=str)

    print(f"\nDetailed results saved to JSON file")
    print(f"Analysis completed successfully!")


if __name__ == "__main__":
    main()
