"""
Signal handlers for graceful shutdown of the payment simulation.
"""

import signal
import sys
from typing import Any


class GracefulShutdownHandler:
    """Handles graceful shutdown of the simulation."""
    
    def __init__(self, simulator: Any):
        """Initialize with simulator instance."""
        self.simulator = simulator
        self.shutdown_requested = False
    
    def signal_handler(self, signum: int, frame: Any):
        """Handle shutdown signals."""
        signal_names = {
            signal.SIGINT: "SIGINT (Ctrl+C)",
            signal.SIGTERM: "SIGTERM"
        }
        
        signal_name = signal_names.get(signum, f"Signal {signum}")
        
        if not self.shutdown_requested:
            print(f"\n🔄 Received {signal_name}, shutting down gracefully...")
            print("💾 Saving final statistics and logs...")
            
            self.shutdown_requested = True
            self.simulator.running = False
            
            # Allow some time for cleanup
            try:
                self.simulator._print_final_stats()
            except Exception as e:
                print(f"Error during final stats: {e}")
        else:
            print(f"\n⚠️  Force shutdown requested, exiting immediately...")
            sys.exit(1)
    
    def setup(self):
        """Setup signal handlers."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)


def setup_signal_handlers(simulator: Any):
    """Setup signal handlers for graceful shutdown."""
    handler = GracefulShutdownHandler(simulator)
    handler.setup()
    return handler


class SimulationInterrupt(Exception):
    """Custom exception for simulation interruption."""
    pass


def with_graceful_shutdown(func):
    """Decorator to add graceful shutdown to functions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print("\n🔄 Graceful shutdown requested...")
            raise SimulationInterrupt("Simulation interrupted by user")
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")
            raise
    
    return wrapper

