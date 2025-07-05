#!/usr/bin/env python3
"""
Main entry point for the Realistic Payment Gateway Simulator.
"""

import sys
import os
from datetime import datetime

# Add the current directory and parent directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, "src")

sys.path.insert(0, current_dir)  # Add simulation directory
sys.path.insert(0, parent_dir)  # Add parent directory
sys.path.insert(0, src_dir)  # Add src directory

# Now import using relative imports from current directory
from core.simulator import RealisticPaymentSimulator
from utils.signal_handlers import setup_signal_handlers


def run_main_simulation():
    """Run the main continuous simulation."""
    print("🎭 REALISTIC PAYMENT GATEWAY SIMULATOR")
    print("=" * 60)
    print("This simulator generates realistic payment traffic with:")
    print("✅ Grab ecosystem merchants (Transport, Food, Mart, etc.)")
    print("✅ Regional customer preferences (SEA focus)")
    print("✅ All payment methods and card networks")
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
        print(
            "\n🔧 If you're getting import errors, make sure you're running from the parent directory:"
        )
        print("   cd ..")
        print("   python -m simulation.main")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Simulator initialization error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def run_quick_test():
    """Run a quick 30-second test simulation."""
    print("🏃‍♂️ Quick Test Mode (30 seconds)")

    try:
        simulator = RealisticPaymentSimulator()
        simulator.run_quick_test(30)
    except Exception as e:
        print(f"Quick test error: {e}")


def run_high_failure_test():
    """Run high failure rate simulation for testing recovery agent."""
    print("🔥 High Failure Mode")

    try:
        simulator = RealisticPaymentSimulator()
        simulator.run_high_failure_simulation()
    except Exception as e:
        print(f"High failure test error: {e}")


def run_stress_test():
    """Run a high-volume stress test."""
    print("⚡ Stress Test Mode")

    try:
        simulator = RealisticPaymentSimulator()
        simulator.run_stress_test(200)
    except Exception as e:
        print(f"Stress test error: {e}")


def run_business_hours_simulation():
    """Simulate traffic patterns throughout a business day."""
    print("🏢 Business Hours Simulation")

    try:
        simulator = RealisticPaymentSimulator()
        simulator.run_business_hours_simulation()
    except Exception as e:
        print(f"Business hours simulation error: {e}")


def show_help():
    """Show help information."""
    print("🎭 Realistic Payment Gateway Simulator")
    print("\nAvailable commands:")
    print("  python main.py                    - Run continuous simulation")
    print("  python main.py quick             - 30-second quick test")
    print("  python main.py stress            - High-volume stress test")
    print("  python main.py failure           - High failure rate test (40%+ failures)")
    print("  python main.py business          - Business hours simulation")
    print("  python main.py analyze <file>    - Analyze log file")
    print("  python main.py help              - Show this help")
    print("\nAlternative usage (recommended):")
    print("  cd ..")
    print("  python -m simulation.main")
    print("\nPress Ctrl+C to stop any running simulation.")


def main():
    """Main CLI entry point."""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

        if mode == "quick":
            run_quick_test()
        elif mode == "stress":
            run_stress_test()
        elif mode == "failure":
            run_high_failure_test()
        elif mode == "business":
            run_business_hours_simulation()
        elif mode == "help":
            show_help()
        else:
            print(f"Unknown mode: {mode}")
            show_help()
    else:
        run_main_simulation()


if __name__ == "__main__":
    main()
