"""
Display utilities for the payment simulation.
"""

from datetime import datetime
from typing import Dict, Any, List


class SimulationDisplay:
    """Handles console output formatting for the simulation."""
    
    @staticmethod
    def print_progress_bar(current: int, total: int, prefix: str = "Progress", length: int = 40):
        """Print a progress bar for long-running operations."""
        if total == 0:
            return
        percent = (current / total) * 100
        filled_length = int(length * current // total)
        bar = '█' * filled_length + '-' * (length - filled_length)
        print(f'\r{prefix}: |{bar}| {percent:.1f}% ({current}/{total})', end='', flush=True)
        if current == total:
            print()  # New line when complete

    @staticmethod
    def print_simulation_startup(customer_count: int, merchant_count: int):
        """Print simulation startup information."""
        print(f"🎭 Realistic Payment Gateway Simulator Initialized")
        print(f"📊 Generated {customer_count} customers and {merchant_count} merchants")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💳 Press Ctrl+C to stop simulation\n")

    @staticmethod
    def print_export_info(filename: str):
        """Print export information."""
        print(f"   Exported training dataset: {filename}")

    @staticmethod
    def print_export_error(error: str):
        """Print export error."""
        print(f"   Export error: {error}")

    @staticmethod
    def print_header():
        """Print simulation header."""
        print("🎭 REALISTIC PAYMENT GATEWAY SIMULATOR")
        print("=" * 60)
        print("Grab-based Payment Ecosystem Simulation")
        print("=" * 60)

    @staticmethod
    def print_simulation_info():
        """Print simulation information."""
        print("This simulator generates realistic payment traffic with:")
        print("✅ Grab ecosystem merchants (Transport, Food, Mart, etc.)")
        print("✅ Regional customer preferences")
        print("✅ All payment methods and card networks")
        print("✅ Dynamic failure injection")
        print("✅ Business-realistic transaction patterns")
        print("✅ Comprehensive logging for LLM training")
        print("✅ Time-based traffic patterns")
        print("=" * 60)

    @staticmethod
    def print_transaction_header():
        """Print transaction table header."""
        print("\nStatus | Amount    | Method       | Provider | Region         | Merchant Type  | Order ID")
        print("-" * 95)

    @staticmethod
    def print_transaction(result: Dict[str, Any], payment_instrument, customer, merchant, order_id: str):
        """Print a single transaction result."""
        transaction = result.get('transaction', {})
        status_emoji = "✅" if result.get('success') else "❌"
        currency = transaction.get('currency', 'USD')
        amount = transaction.get('amount', 0)
        method = getattr(payment_instrument, 'method', type('m', (), {'value':'unknown'})()).value
        provider = transaction.get('provider', 'unknown')
        region = getattr(customer.region, 'value', 'unknown') if customer else 'unknown'
        merchant_type = merchant.get('type', 'unknown') if merchant else 'unknown'
        print(f"{status_emoji} {currency} {amount:>8.2f} | "
              f"{method:>12} | "
              f"{provider:>8} | "
              f"{region:>15} | "
              f"{merchant_type:>14} | "
              f"Order: {order_id}")

    @staticmethod
    def print_stats_summary(stats: Dict[str, Any]):
        """Print statistics summary."""
        total = stats.get('total_payments', 0)
        if total == 0:
            return
        success_rate = (stats.get('successful_payments', 0) / total) * 100
        print(f"\n📊 SIMULATION STATS (Total: {total} payments)")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Successful: {stats.get('successful_payments', 0)}")
        print(f"   Failed: {stats.get('failed_payments', 0)}")
        if stats.get('by_network'):
            top_networks = dict(list(stats['by_network'].items())[:3])
            print(f"   By Network: {top_networks}")
        if stats.get('by_method'):
            print(f"   By Method: {stats['by_method']}")
        if stats.get('by_region'):
            top_regions = dict(list(stats['by_region'].items())[:3])
            print(f"   By Region: {top_regions}")
        if stats.get('by_merchant_type'):
            top_merchants = dict(list(stats['by_merchant_type'].items())[:3])
            print(f"   By Merchant: {top_merchants}")
        if stats.get('scenarios_triggered'):
            recent_scenarios = [s['scenario'] for s in stats['scenarios_triggered'][-3:]]
            print(f"   Recent Failures: {recent_scenarios}")

    @staticmethod
    def print_provider_health(health_data: Dict[str, Dict]):
        """Print provider health status."""
        print(f"\n🏥 Provider Health Status:")
        for provider, health in health_data.items():
            success_rate = health.get('success_rate', 0) * 100
            latency = health.get('avg_latency', 0)
            is_healthy = health.get('is_healthy', False)
            status = "🟢" if is_healthy else "🔴"
            print(f"   {status} {provider:>8}: {success_rate:>5.1f}% success, {latency:>6.0f}ms avg")

    @staticmethod
    def print_final_report(stats: Dict[str, Any], health_data: Dict[str, Dict]):
        """Print comprehensive final report."""
        print(f"\n{'='*80}")
        print(f" FINAL SIMULATION REPORT")
        print(f"{'='*80}")
        total = stats.get('total_payments', 0)
        if total == 0:
            print("No payments processed.")
            return
        success_rate = (stats.get('successful_payments', 0) / total) * 100
        print(f"\n📈 OVERALL PERFORMANCE:")
        print(f"   Total Payments Processed: {total:,}")
        print(f"   Successful Payments: {stats.get('successful_payments', 0):,} ({success_rate:.1f}%)")
        print(f"   Failed Payments: {stats.get('failed_payments', 0):,} ({100-success_rate:.1f}%)")
        SimulationDisplay._print_breakdown("🏦 BY CARD NETWORK", stats.get('by_network', {}), total)
        SimulationDisplay._print_breakdown("💳 BY PAYMENT METHOD", stats.get('by_method', {}), total)
        SimulationDisplay._print_breakdown("🌍 BY REGION", stats.get('by_region', {}), total)
        SimulationDisplay._print_breakdown("🏪 BY MERCHANT TYPE", stats.get('by_merchant_type', {}), total)
        SimulationDisplay._print_breakdown("💰 BY AMOUNT RANGE", stats.get('by_amount_range', {},), total)
        if stats.get('scenarios_triggered'):
            print(f"\n🔥 FAILURE SCENARIOS TRIGGERED: {len(stats['scenarios_triggered'])}")
            for scenario in stats['scenarios_triggered'][-5:]:
                timestamp = datetime.fromisoformat(scenario['timestamp']).strftime('%H:%M:%S')
                print(f"   {timestamp}: {scenario['scenario']}")
        print(f"\n🏥 FINAL PROVIDER HEALTH:")
        for provider, health in health_data.items():
            success_rate_prov = health.get('success_rate', 0) * 100
            latency = health.get('avg_latency', 0)
            status = "🟢" if health.get('is_healthy', False) else "🔴"
            print(f"   {status} {provider:>8}: {success_rate_prov:>5.1f}% success, {latency:>6.0f}ms avg")
        print(f"\n📁 TRAINING DATA:")
        print(f"   Structured logs saved to: ./logs/")
        print(f"   Use these logs to train your LLM diagnostic brain!")
        print(f"   Total log entries: ~{total * 3} (payment events + routing decisions + metrics)")

    @staticmethod
    def _print_breakdown(title: str, data: Dict[str, int], total: int):
        """Print a data breakdown section."""
        if not data:
            return
        print(f"\n{title}:")
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        for item, count in sorted_items:
            percentage = (count / total) * 100
            print(f"   {item:>15}: {count:>4} ({percentage:>5.1f}%)")

    @staticmethod
    def print_critical_event(event_type: str, transaction_id: str, provider: str, timestamp: str):
        """Print critical events in real-time."""
        print(f"🚨 [{timestamp}] {event_type}: {transaction_id} via {provider}")

    @staticmethod
    def print_scenario_injection(scenario: str, message: str):
        """Print failure scenario injection."""
        print(f"🔥 Injected failure scenario: {scenario} - {message}")

    @staticmethod
    def print_scenario_recovery():
        """Print scenario recovery."""
        print(f"✅ Recovered from failure scenarios")

    @staticmethod
    def print_time_simulation(hour: int, payment_count: int):
        """Print time-based simulation info."""
        print(f"\n⏰ Simulating {hour:02d}:00 traffic ({payment_count} payments)")

    @staticmethod
    def print_simulation_modes():
        """Print available simulation modes."""
        print("🎭 Available Simulation Modes:")
        print("  main                     - Continuous realistic simulation")
        print("  quick                    - 30-second quick test")
        print("  stress                   - High-volume stress test")
        print("  business                 - Business hours simulation")
        print("  analyze <file>           - Analyze log file")
        print("  help                     - Show help")
        print("\nPress Ctrl+C to stop any running simulation.")


class ColorFormatter:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Colorize text with ANSI codes."""
        return f"{getattr(cls, color.upper(), '')}{text}{cls.ENDC}"
    
    @classmethod
    def success(cls, text: str) -> str:
        """Green text for success."""
        return cls.colorize(text, 'OKGREEN')
    
    @classmethod
    def error(cls, text: str) -> str:
        """Red text for errors."""
        return cls.colorize(text, 'FAIL')
    
    @classmethod
    def warning(cls, text: str) -> str:
        """Yellow text for warnings."""
        return cls.colorize(text, 'WARNING')
    
    @classmethod
    def info(cls, text: str) -> str:
        """Blue text for info."""
        return cls.colorize(text, 'OKBLUE')
    
    @classmethod
    def header(cls, text: str) -> str:
        """Purple text for headers."""
        return cls.colorize(text, 'HEADER')


class TableFormatter:
    """Utility for formatting tables in console output."""
    
    @staticmethod
    def format_table(headers: List[str], rows: List[List[str]], widths: List[int] = None) -> str:
        """Format data as a table."""
        if not rows:
            return ""
        if widths is None:
            widths = [len(header) for header in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    if i < len(widths):
                        widths[i] = max(widths[i], len(str(cell)))
        format_str = " | ".join(f"{{:<{width}}}" for width in widths)
        lines = []
        lines.append(format_str.format(*headers))
        lines.append("-" * (sum(widths) + 3 * (len(headers) - 1)))
        for row in rows:
            lines.append(format_str.format(*[str(cell) for cell in row]))
        return "\n".join(lines)
    
    @staticmethod
    def format_key_value_table(data: Dict[str, Any], title: str = None) -> str:
        """Format key-value pairs as a table."""
        if not data:
            return ""
        lines = []
        if title:
            lines.append(title)
            lines.append("=" * len(title))
        key_width = max(len(str(key)) for key in data.keys())
        for key, value in data.items():
            lines.append(f"{str(key):<{key_width}} : {value}")
        return "\n".join(lines)


class MetricsFormatter:
    """Specialized formatting for metrics and statistics."""
    
    @staticmethod
    def format_percentage(value: float, total: float) -> str:
        """Format percentage with proper handling of edge cases."""
        if total == 0:
            return "0.0%"
        return f"{(value / total) * 100:.1f}%"
    
    @staticmethod
    def format_currency(amount: float, currency: str = "USD") -> str:
        """Format currency amount."""
        if currency == "USD":
            return f"${amount:,.2f}"
        elif currency == "EUR":
            return f"€{amount:,.2f}"
        elif currency == "GBP":
            return f"£{amount:,.2f}"
        else:
            return f"{currency} {amount:,.2f}"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    @staticmethod
    def format_number(number: int) -> str:
        """Format large numbers with thousand separators."""
        return f"{number:,}"
    
    @staticmethod
    def format_rate(rate: float, unit: str = "per second") -> str:
        """Format rate with appropriate unit."""
        return f"{rate:.2f} {unit}"
