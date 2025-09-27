"""
Command Line Interface for NSE Data ETL.

Provides a CLI interface for running the NSE Data ETL system with various commands
for data collection, processing, and monitoring.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.table import Table
except ImportError:
    # Fallback if typer and rich are not installed
    typer = None
    Console = None
    Table = None

from .config import get_settings
from .logging import setup_logging, get_logger


# Initialize CLI app if typer is available
if typer:
    app = typer.Typer(
        name="nse-etl",
        help="NSE Data ETL - High-performance financial data processing system",
        add_completion=False,
    )
    console = Console()
else:
    app = None
    console = None


def create_fallback_cli():
    """Create a fallback CLI when typer is not available."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="NSE Data ETL - High-performance financial data processing system"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="serve",
        choices=["serve", "collect", "process", "status", "version"],
        help="Command to run"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0", 
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    return parser


async def start_server(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    """Start the NSE Data ETL server."""
    settings = get_settings()
    logger = get_logger("cli")
    
    logger.info(
        "Starting NSE Data ETL server",
        host=host,
        port=port,
        reload=reload,
        environment=str(settings.environment),
    )
    
    # This would normally start the actual server
    # For now, just simulate a running server
    print(f"🚀 NSE Data ETL server starting on http://{host}:{port}")
    print(f"📊 Metrics available at http://{host}:{settings.monitoring.metrics_port}/metrics")
    print(f"🏥 Health check at http://{host}:{settings.monitoring.metrics_port}/health")
    print("💡 Press Ctrl+C to stop")
    
    try:
        # Simulate server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        print("\n👋 NSE Data ETL server stopped")


async def collect_data():
    """Start data collection process."""
    settings = get_settings()
    logger = get_logger("cli")
    
    logger.info("Starting data collection")
    print("📈 Starting NSE data collection...")
    print("💡 Press Ctrl+C to stop")
    
    try:
        # Simulate data collection
        while True:
            print("🔄 Collecting equity data...")
            await asyncio.sleep(settings.collector.equity_data_interval)
    except KeyboardInterrupt:
        logger.info("Data collection stopped")
        print("\n🛑 Data collection stopped")


async def process_data():
    """Start data processing."""
    logger = get_logger("cli")
    
    logger.info("Starting data processing")
    print("⚙️  Starting data processing...")
    print("💡 Press Ctrl+C to stop")
    
    try:
        # Simulate data processing
        while True:
            print("🔄 Processing batch data...")
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        logger.info("Data processing stopped")
        print("\n🛑 Data processing stopped")


def show_status():
    """Show system status."""
    settings = get_settings()
    
    if console and Table:
        table = Table(title="NSE Data ETL Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        
        table.add_row("Application", "✅ Ready", f"v{settings.app_version}")
        table.add_row("Environment", "✅ Configured", str(settings.environment))
        table.add_row("Database", "🔄 Checking", "ClickHouse + Redis")
        table.add_row("Monitoring", "✅ Ready", f"Port {settings.monitoring.metrics_port}")
        
        console.print(table)
    else:
        print("NSE Data ETL Status:")
        print(f"  Application: Ready (v{settings.app_version})")
        print(f"  Environment: {settings.environment}")
        print(f"  Database: ClickHouse + Redis")
        print(f"  Monitoring: Port {settings.monitoring.metrics_port}")


def show_version():
    """Show version information."""
    settings = get_settings()
    print(f"NSE Data ETL v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Python: {sys.version}")


# Typer commands (if available)
if app:
    @app.command()
    def serve(
        host: str = typer.Option("0.0.0.0", help="Host to bind to"),
        port: int = typer.Option(8080, help="Port to bind to"),
        reload: bool = typer.Option(False, help="Enable auto-reload"),
    ):
        """Start the NSE Data ETL server."""
        asyncio.run(start_server(host, port, reload))

    @app.command()
    def collect():
        """Start data collection process."""
        asyncio.run(collect_data())

    @app.command()
    def process():
        """Start data processing."""
        asyncio.run(process_data())

    @app.command()
    def status():
        """Show system status."""
        show_status()

    @app.command()
    def version():
        """Show version information."""
        show_version()


def main():
    """Main CLI entry point."""
    # Setup logging first
    try:
        settings = get_settings()
        setup_logging(settings)
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Use typer if available, otherwise fallback
    if app:
        app()
    else:
        parser = create_fallback_cli()
        args = parser.parse_args()
        
        if args.command == "serve":
            asyncio.run(start_server(args.host, args.port, args.reload))
        elif args.command == "collect":
            asyncio.run(collect_data())
        elif args.command == "process":
            asyncio.run(process_data())
        elif args.command == "status":
            show_status()
        elif args.command == "version":
            show_version()


if __name__ == "__main__":
    main()