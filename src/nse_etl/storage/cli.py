"""
CLI commands for ClickHouse schema management.

Provides command-line interface for database schema operations
including initialization, migration, benchmarking, and maintenance.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
except ImportError:
    # Fallback for environments without rich/typer
    typer = None
    Console = None
    Table = None
    Progress = None
    Panel = None

from ..config import get_settings
from .schema_manager import SchemaManager, SampleDataGenerator
from .benchmark import ClickHouseBenchmark

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize console for rich output
console = Console() if Console else None

# Create CLI app if typer is available
app = typer.Typer(
    name="schema",
    help="ClickHouse schema management commands",
    no_args_is_help=True
) if typer else None


def print_status(message: str, status: str = "info"):
    """Print status message with appropriate formatting."""
    if console:
        if status == "success":
            console.print(f"✅ {message}", style="green")
        elif status == "error":
            console.print(f"❌ {message}", style="red")
        elif status == "warning":
            console.print(f"⚠️  {message}", style="yellow")
        else:
            console.print(f"ℹ️  {message}", style="blue")
    else:
        print(f"[{status.upper()}] {message}")


def init_schema(
    drop_existing: bool = False,
    with_sample_data: bool = True,
    confirm: bool = False
):
    """
    Initialize ClickHouse schema for NSE data.
    
    Args:
        drop_existing: Drop existing schema first
        with_sample_data: Insert sample data for testing
        confirm: Skip confirmation prompts
    """
    try:
        print_status("Initializing ClickHouse schema for NSE Data ETL...")
        
        # Get settings
        settings = get_settings()
        schema_manager = SchemaManager(settings)
        
        # Drop existing schema if requested
        if drop_existing:
            if not confirm:
                if console:
                    confirm_drop = typer.confirm("⚠️  This will drop the entire database. Continue?")
                    if not confirm_drop:
                        print_status("Schema initialization cancelled", "warning")
                        return False
                else:
                    response = input("This will drop the entire database. Continue? (y/N): ")
                    if response.lower() != 'y':
                        print_status("Schema initialization cancelled", "warning")
                        return False
            
            print_status("Dropping existing schema...")
            schema_manager.drop_schema(confirm=True)
        
        # Initialize schema with progress tracking
        if console and Progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Creating database schema...", total=None)
                success = schema_manager.initialize_schema()
                progress.update(task, completed=100)
        else:
            success = schema_manager.initialize_schema()
        
        if not success:
            print_status("Schema initialization failed", "error")
            return False
        
        # Insert sample data if requested
        if with_sample_data:
            print_status("Inserting sample data...")
            generator = SampleDataGenerator(schema_manager)
            sample_success = generator.insert_sample_data()
            
            if sample_success:
                print_status("Sample data inserted successfully", "success")
            else:
                print_status("Sample data insertion failed", "warning")
        
        print_status("Schema initialization completed successfully!", "success")
        
        # Display schema information
        if console:
            display_schema_info(schema_manager)
        
        return True
        
    except Exception as e:
        print_status(f"Schema initialization failed: {e}", "error")
        logger.exception("Schema initialization error")
        return False


def display_schema_info(schema_manager: SchemaManager):
    """Display schema information in a formatted table."""
    if not console or not Table:
        return
    
    # Get schema stats
    table_stats = schema_manager.get_table_stats()
    table_results = schema_manager.verify_tables()
    view_results = schema_manager.verify_materialized_views()
    
    # Create tables overview
    table = Table(title="Database Schema Overview")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Records", style="yellow")
    table.add_column("Size", style="magenta")
    
    # Add table information
    for table_name, exists in table_results.items():
        status = "✅ EXISTS" if exists else "❌ MISSING"
        stats = table_stats.get(table_name, {})
        records = f"{stats.get('row_count', 0):,}" if 'row_count' in stats else "N/A"
        size = stats.get('size', 'N/A')
        
        table.add_row(f"Table: {table_name}", status, records, size)
    
    # Add materialized view information
    for view_name, exists in view_results.items():
        status = "✅ EXISTS" if exists else "❌ MISSING"
        table.add_row(f"View: {view_name}", status, "N/A", "N/A")
    
    console.print(table)


def verify_schema():
    """Verify schema integrity and display status."""
    try:
        print_status("Verifying schema integrity...")
        
        schema_manager = SchemaManager()
        
        # Verify tables and views
        table_results = schema_manager.verify_tables()
        view_results = schema_manager.verify_materialized_views()
        
        # Check overall status
        all_tables_exist = all(table_results.values())
        all_views_exist = all(view_results.values())
        
        if all_tables_exist and all_views_exist:
            print_status("Schema verification passed", "success")
            
            if console:
                display_schema_info(schema_manager)
        else:
            print_status("Schema verification failed", "error")
            
            missing_tables = [t for t, exists in table_results.items() if not exists]
            missing_views = [v for v, exists in view_results.items() if not exists]
            
            if missing_tables:
                print_status(f"Missing tables: {', '.join(missing_tables)}", "error")
            if missing_views:
                print_status(f"Missing views: {', '.join(missing_views)}", "error")
                
        return all_tables_exist and all_views_exist
        
    except Exception as e:
        print_status(f"Schema verification failed: {e}", "error")
        return False


def run_benchmark(
    test_type: str = "comprehensive",
    batch_size: int = 100000,
    iterations: int = 5
):
    """
    Run performance benchmarks on the schema.
    
    Args:
        test_type: Type of test (comprehensive, insert, query, concurrent)
        batch_size: Batch size for insert tests
        iterations: Number of iterations
    """
    try:
        print_status(f"Running {test_type} benchmark...")
        
        benchmark = ClickHouseBenchmark()
        
        if test_type == "comprehensive":
            results = benchmark.run_comprehensive_benchmark()
            
            if console and Panel:
                # Display results in a nice panel
                summary = results['summary']
                content = f"""
📈 Bulk Insert Throughput: {summary['bulk_insert_throughput']:.0f} records/sec
📈 Concurrent Throughput: {summary['concurrent_throughput']:.0f} records/sec  
📈 Average Query Latency: {summary['avg_query_latency']*1000:.2f}ms
📈 Overall Success Rate: {summary['overall_success_rate']:.1f}%
⏱️  Total Benchmark Time: {summary['total_benchmark_time']:.2f}s
                """
                
                console.print(Panel(
                    content.strip(),
                    title="📊 Benchmark Results",
                    border_style="green"
                ))
            else:
                summary = results['summary']
                print(f"Bulk Insert Throughput: {summary['bulk_insert_throughput']:.0f} records/sec")
                print(f"Concurrent Throughput: {summary['concurrent_throughput']:.0f} records/sec")
                print(f"Average Query Latency: {summary['avg_query_latency']*1000:.2f}ms")
                print(f"Overall Success Rate: {summary['overall_success_rate']:.1f}%")
                
        elif test_type == "insert":
            result = benchmark.benchmark_bulk_insert(batch_size, iterations)
            print_status(f"Insert benchmark: {result.throughput:.0f} records/sec", "success")
            
        elif test_type == "query":
            results = benchmark.benchmark_query_performance()
            for result in results:
                print_status(f"{result.operation}: {result.duration*1000:.2f}ms avg", "success")
                
        elif test_type == "concurrent":
            result = benchmark.benchmark_concurrent_operations()
            print_status(f"Concurrent benchmark: {result.throughput:.0f} records/sec", "success")
        
        # Cleanup test data
        benchmark.cleanup_test_data()
        print_status("Benchmark completed successfully", "success")
        
    except Exception as e:
        print_status(f"Benchmark failed: {e}", "error")
        logger.exception("Benchmark error")


def optimize_schema():
    """Optimize database tables for better performance."""
    try:
        print_status("Optimizing database tables...")
        
        schema_manager = SchemaManager()
        schema_manager.optimize_tables()
        
        print_status("Database optimization completed", "success")
        
    except Exception as e:
        print_status(f"Database optimization failed: {e}", "error")


def generate_sample_data(count: int = 10000):
    """Generate sample data for testing."""
    try:
        print_status(f"Generating {count} sample records...")
        
        schema_manager = SchemaManager()
        generator = SampleDataGenerator(schema_manager)
        
        # Generate custom amount of data
        success = generator.insert_sample_data()
        
        if success:
            print_status("Sample data generated successfully", "success")
        else:
            print_status("Sample data generation failed", "error")
            
    except Exception as e:
        print_status(f"Sample data generation failed: {e}", "error")


def export_schema():
    """Export schema information to JSON."""
    try:
        print_status("Exporting schema information...")
        
        schema_manager = SchemaManager()
        schema_info = schema_manager.get_schema_info()
        
        # Save to file
        import json
        output_file = Path("schema_info.json")
        
        with open(output_file, 'w') as f:
            json.dump(schema_info, f, indent=2, default=str)
        
        print_status(f"Schema exported to {output_file}", "success")
        
    except Exception as e:
        print_status(f"Schema export failed: {e}", "error")


# Register CLI commands if typer is available
if app and typer:
    @app.command()
    def init(
        drop_existing: bool = typer.Option(False, "--drop", help="Drop existing schema"),
        no_sample_data: bool = typer.Option(False, "--no-sample", help="Skip sample data"),
        yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts")
    ):
        """Initialize ClickHouse schema."""
        init_schema(drop_existing, not no_sample_data, yes)

    @app.command()
    def verify():
        """Verify schema integrity."""
        verify_schema()

    @app.command()
    def benchmark(
        test_type: str = typer.Argument("comprehensive", help="Test type: comprehensive, insert, query, concurrent"),
        batch_size: int = typer.Option(100000, help="Batch size for tests"),
        iterations: int = typer.Option(5, help="Number of iterations")
    ):
        """Run performance benchmarks."""
        run_benchmark(test_type, batch_size, iterations)

    @app.command()
    def optimize():
        """Optimize database tables."""
        optimize_schema()

    @app.command()
    def sample_data(
        count: int = typer.Option(10000, help="Number of sample records")
    ):
        """Generate sample data."""
        generate_sample_data(count)

    @app.command()
    def export():
        """Export schema information."""
        export_schema()


# Fallback functions for non-typer environments
def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ClickHouse Schema Management")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize schema')
    init_parser.add_argument('--drop', action='store_true', help='Drop existing schema')
    init_parser.add_argument('--no-sample', action='store_true', help='Skip sample data')
    init_parser.add_argument('-y', '--yes', action='store_true', help='Skip confirmations')
    
    # Verify command
    subparsers.add_parser('verify', help='Verify schema')
    
    # Benchmark command
    bench_parser = subparsers.add_parser('benchmark', help='Run benchmarks')
    bench_parser.add_argument('test_type', nargs='?', default='comprehensive')
    
    # Optimize command
    subparsers.add_parser('optimize', help='Optimize tables')
    
    # Sample data command
    sample_parser = subparsers.add_parser('sample-data', help='Generate sample data')
    sample_parser.add_argument('--count', type=int, default=10000)
    
    # Export command
    subparsers.add_parser('export', help='Export schema info')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_schema(args.drop, not args.no_sample, args.yes)
    elif args.command == 'verify':
        verify_schema()
    elif args.command == 'benchmark':
        run_benchmark(args.test_type)
    elif args.command == 'optimize':
        optimize_schema()
    elif args.command == 'sample-data':
        generate_sample_data(args.count)
    elif args.command == 'export':
        export_schema()
    else:
        parser.print_help()


if __name__ == "__main__":
    if app:
        app()
    else:
        main()