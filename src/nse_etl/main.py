"""
Main entry point for NSE Data ETL.

This module provides the main entry point for the NSE Data ETL system.
It handles the startup sequence and coordinates all components.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import Optional

from .config import get_settings
from .logging import setup_logging, get_logger
from .cli import main as cli_main


class NSEDataETL:
    """Main application class for NSE Data ETL system."""
    
    def __init__(self):
        """Initialize the NSE Data ETL system."""
        self.settings = get_settings()
        self.logger = None
        self.running = False
        self._shutdown_event = asyncio.Event()
    
    async def startup(self):
        """Perform startup tasks."""
        # Setup logging
        setup_logging(self.settings)
        self.logger = get_logger("main")
        
        self.logger.info(
            "NSE Data ETL starting up",
            version=self.settings.app_version,
            environment=str(self.settings.environment),
            debug=self.settings.debug,
        )
        
        # Initialize components
        await self._initialize_database()
        await self._initialize_collectors()
        await self._initialize_processors()
        await self._initialize_monitoring()
        
        self.running = True
        self.logger.info("NSE Data ETL startup completed")
    
    async def shutdown(self):
        """Perform shutdown tasks."""
        if not self.logger:
            return
            
        self.logger.info("NSE Data ETL shutting down")
        self.running = False
        
        # Shutdown components in reverse order
        await self._shutdown_monitoring()
        await self._shutdown_processors()
        await self._shutdown_collectors() 
        await self._shutdown_database()
        
        self.logger.info("NSE Data ETL shutdown completed")
    
    async def _initialize_database(self):
        """Initialize database connections."""
        if self.logger:
            self.logger.info(
                "Initializing database connections",
                clickhouse_host=self.settings.database.clickhouse_host,
                redis_host=self.settings.database.redis_host,
            )
        # Database initialization would go here
    
    async def _initialize_collectors(self):
        """Initialize data collectors."""
        if self.logger:
            self.logger.info("Initializing data collectors")
        # Collector initialization would go here
    
    async def _initialize_processors(self):
        """Initialize data processors."""
        if self.logger:
            self.logger.info("Initializing data processors")
        # Processor initialization would go here
    
    async def _initialize_monitoring(self):
        """Initialize monitoring systems."""
        if self.logger:
            self.logger.info(
                "Initializing monitoring",
                metrics_port=self.settings.monitoring.metrics_port,
            )
        # Monitoring initialization would go here
    
    async def _shutdown_database(self):
        """Shutdown database connections."""
        if self.logger:
            self.logger.info("Shutting down database connections")
        # Database shutdown would go here
    
    async def _shutdown_collectors(self):
        """Shutdown data collectors."""
        if self.logger:
            self.logger.info("Shutting down data collectors")
        # Collector shutdown would go here
    
    async def _shutdown_processors(self):
        """Shutdown data processors.""" 
        if self.logger:
            self.logger.info("Shutting down data processors")
        # Processor shutdown would go here
    
    async def _shutdown_monitoring(self):
        """Shutdown monitoring systems."""
        if self.logger:
            self.logger.info("Shutting down monitoring")
        # Monitoring shutdown would go here
    
    async def run(self):
        """Run the main application loop."""
        try:
            await self.startup()
            
            # Main application loop
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            if self.logger:
                self.logger.error("Application error", error=str(e))
            raise
        finally:
            await self.shutdown()


def setup_signal_handlers(app: NSEDataETL):
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        app.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def run_app():
    """Run the NSE Data ETL application."""
    app = NSEDataETL()
    setup_signal_handlers(app)
    
    try:
        await app.run()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Application failed: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    # Check if we're being run as a module or CLI
    if len(sys.argv) > 1:
        # Delegate to CLI
        cli_main()
    else:
        # Run the main application
        try:
            asyncio.run(run_app())
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Failed to start: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()