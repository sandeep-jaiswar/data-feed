"""
ClickHouse Schema Manager for NSE Data ETL Pipeline.

Handles database schema initialization, migration, and management
with investment banking-grade reliability and error handling.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

try:
    from clickhouse_driver import Client
    from clickhouse_driver.errors import Error as ClickHouseError
except ImportError:
    # Fallback for environments without ClickHouse driver
    Client = None
    ClickHouseError = Exception

from ..config import Settings, get_settings
from .models import RawTick, SymbolMaster, MarketEvent, normalize_nse_symbol

logger = logging.getLogger(__name__)


class SchemaManager:
    """
    ClickHouse schema manager for NSE data ETL pipeline.
    
    Handles database initialization, schema creation, data migration,
    and maintenance operations with proper error handling and logging.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize schema manager.
        
        Args:
            settings: Application settings, uses default if None
        """
        self.settings = settings or get_settings()
        self.client: Optional[Client] = None
        self.database = self.settings.database.clickhouse_database
        
        # SQL file paths
        self.sql_dir = Path(__file__).parent.parent.parent.parent / "sql"
        self.schema_files = [
            "01_create_tables.sql",
            "02_create_indexes.sql", 
            "03_create_materialized_views.sql",
            "04_insert_reference_data.sql"
        ]
        
    def _get_client(self) -> Client:
        """
        Get ClickHouse client connection.
        
        Returns:
            ClickHouse client instance
            
        Raises:
            RuntimeError: If ClickHouse driver not available
            ClickHouseError: If connection fails
        """
        if Client is None:
            raise RuntimeError("ClickHouse driver not available")
            
        if self.client is None:
            try:
                self.client = Client(
                    host=self.settings.database.clickhouse_host,
                    port=self.settings.database.clickhouse_port,
                    user=self.settings.database.clickhouse_user,
                    password=self.settings.database.clickhouse_password,
                    database='system',  # Connect to system database first
                    settings={
                        "max_execution_time": 300,  # 5 minutes
                        "max_memory_usage": 1000000000,  # 1GB
                        "readonly": 0
                    }
                )
                logger.info("ClickHouse client connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to ClickHouse: {e}")
                raise ClickHouseError(f"Connection failed: {e}")
                
        return self.client
        
    def create_database(self) -> None:
        """
        Create the main database if it doesn't exist.
        
        Raises:
            ClickHouseError: If database creation fails
        """
        try:
            client = self._get_client()
            client.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            logger.info(f"Database '{self.database}' created/verified successfully")
        except Exception as e:
            logger.error(f"Failed to create database '{self.database}': {e}")
            raise ClickHouseError(f"Database creation failed: {e}")
            
    def execute_sql_file(self, file_path: Path) -> None:
        """
        Execute SQL statements from a file.
        
        Args:
            file_path: Path to SQL file
            
        Raises:
            FileNotFoundError: If SQL file doesn't exist
            ClickHouseError: If SQL execution fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split by semicolons and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            client = self._get_client()
            
            for i, statement in enumerate(statements, 1):
                if statement and not statement.startswith('--'):
                    try:
                        # Skip USE database statements if connecting to specific DB
                        if statement.upper().startswith('USE '):
                            continue
                            
                        client.execute(statement, settings={'database': self.database})
                        logger.debug(f"Executed statement {i}/{len(statements)}")
                    except Exception as e:
                        logger.error(f"Failed to execute statement {i}: {statement[:100]}...")
                        logger.error(f"Error: {e}")
                        raise
                        
            logger.info(f"Successfully executed SQL file: {file_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to execute SQL file {file_path}: {e}")
            raise ClickHouseError(f"SQL execution failed: {e}")
            
    def verify_tables(self) -> Dict[str, bool]:
        """
        Verify that all required tables exist.
        
        Returns:
            Dictionary mapping table names to existence status
        """
        required_tables = [
            'raw_ticks',
            'ohlcv_bars',
            'symbol_master',
            'market_events',
            'data_quality_metrics',
            'market_movers',
            'symbol_statistics'
        ]
        
        results = {}
        client = self._get_client()
        
        for table in required_tables:
            try:
                result = client.execute(
                    "SELECT count() FROM system.tables WHERE database = %(db)s AND name = %(table)s",
                    {'db': self.database, 'table': table}
                )
                exists = result[0][0] > 0
                results[table] = exists
                
                status = "EXISTS" if exists else "MISSING"
                logger.info(f"Table '{table}': {status}")
                
            except Exception as e:
                logger.error(f"Error checking table '{table}': {e}")
                results[table] = False
                
        return results
    
    def verify_materialized_views(self) -> Dict[str, bool]:
        """
        Verify that materialized views are created.
        
        Returns:
            Dictionary mapping view names to existence status
        """
        required_views = [
            'ohlcv_1m_mv',
            'ohlcv_5m_mv',
            'ohlcv_15m_mv',
            'ohlcv_1h_mv',
            'ohlcv_daily_mv'
        ]
        
        results = {}
        client = self._get_client()
        
        for view in required_views:
            try:
                result = client.execute(
                    "SELECT count() FROM system.tables WHERE database = %(db)s AND name = %(view)s AND engine = 'MaterializedView'",
                    {'db': self.database, 'view': view}
                )
                exists = result[0][0] > 0
                results[view] = exists
                
                status = "EXISTS" if exists else "MISSING"
                logger.info(f"Materialized View '{view}': {status}")
                
            except Exception as e:
                logger.error(f"Error checking materialized view '{view}': {e}")
                results[view] = False
                
        return results
        
    def get_table_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all tables.
        
        Returns:
            Dictionary with table statistics
        """
        tables = ['raw_ticks', 'ohlcv_bars', 'symbol_master', 'market_events']
        stats = {}
        client = self._get_client()
        
        for table in tables:
            try:
                # Get row count
                count_result = client.execute(
                    f"SELECT COUNT(*) FROM {self.database}.{table}"
                )
                row_count = count_result[0][0]
                
                # Get table size and parts info
                size_result = client.execute(f"""
                    SELECT 
                        formatReadableSize(sum(bytes)) as size,
                        sum(rows) as rows,
                        count() as parts
                    FROM system.parts 
                    WHERE database = %(db)s AND table = %(table)s AND active = 1
                """, {'db': self.database, 'table': table})
                
                if size_result and size_result[0]:
                    size, rows_in_parts, parts = size_result[0]
                    stats[table] = {
                        'row_count': row_count,
                        'size': size,
                        'rows_in_parts': rows_in_parts,
                        'parts_count': parts
                    }
                else:
                    stats[table] = {
                        'row_count': row_count,
                        'size': 'N/A',
                        'rows_in_parts': 0,
                        'parts_count': 0
                    }
                    
                logger.info(f"Table '{table}' stats: {stats[table]}")
                
            except Exception as e:
                logger.error(f"Error getting stats for table '{table}': {e}")
                stats[table] = {'error': str(e)}
                
        return stats
    
    def initialize_schema(self) -> bool:
        """
        Initialize the complete database schema.
        
        Returns:
            True if initialization successful, False otherwise
        """
        logger.info("Starting ClickHouse schema initialization...")
        
        try:
            # Create database
            self.create_database()
            
            # Execute schema files in order
            for sql_file in self.schema_files:
                file_path = self.sql_dir / sql_file
                if file_path.exists():
                    self.execute_sql_file(file_path)
                else:
                    logger.warning(f"SQL file not found: {sql_file}")
            
            # Verify installation
            logger.info("Verifying schema installation...")
            
            table_results = self.verify_tables()
            view_results = self.verify_materialized_views()
            
            # Check if all required components exist
            all_tables_exist = all(table_results.values())
            all_views_exist = all(view_results.values())
            
            if all_tables_exist and all_views_exist:
                logger.info("✅ Schema initialization completed successfully!")
                
                # Display table statistics
                logger.info("Database statistics:")
                stats = self.get_table_stats()
                for table, table_stats in stats.items():
                    logger.info(f"  {table}: {table_stats}")
                    
                return True
            else:
                missing_tables = [t for t, exists in table_results.items() if not exists]
                missing_views = [v for v, exists in view_results.items() if not exists]
                
                if missing_tables:
                    logger.error(f"❌ Missing tables: {missing_tables}")
                if missing_views:
                    logger.error(f"❌ Missing materialized views: {missing_views}")
                    
                return False
                
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            return False
    
    def drop_schema(self, confirm: bool = False) -> bool:
        """
        Drop the entire database schema (DANGEROUS).
        
        Args:
            confirm: Must be True to actually drop the schema
            
        Returns:
            True if successful
        """
        if not confirm:
            logger.warning("Schema drop not confirmed - no action taken")
            return False
            
        try:
            client = self._get_client()
            client.execute(f"DROP DATABASE IF EXISTS {self.database}")
            logger.warning(f"Database '{self.database}' dropped successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to drop database: {e}")
            return False
    
    def optimize_tables(self) -> None:
        """
        Optimize all tables for better performance.
        
        This runs OPTIMIZE TABLE commands to merge parts and
        improve query performance.
        """
        tables = ['raw_ticks', 'ohlcv_bars', 'symbol_master', 'market_events']
        client = self._get_client()
        
        for table in tables:
            try:
                logger.info(f"Optimizing table {table}...")
                client.execute(f"OPTIMIZE TABLE {self.database}.{table}")
                logger.info(f"Table {table} optimized successfully")
            except Exception as e:
                logger.error(f"Failed to optimize table {table}: {e}")
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get comprehensive schema information.
        
        Returns:
            Dictionary with schema metadata
        """
        client = self._get_client()
        
        try:
            # Get database info
            db_info = client.execute(
                "SELECT name, engine FROM system.databases WHERE name = %(db)s",
                {'db': self.database}
            )
            
            # Get table info
            tables_info = client.execute(f"""
                SELECT name, engine, total_rows, total_bytes 
                FROM system.tables 
                WHERE database = '{self.database}'
                ORDER BY name
            """)
            
            # Get index info
            indexes_info = client.execute(f"""
                SELECT table, name, type, expr 
                FROM system.data_skipping_indices 
                WHERE database = '{self.database}'
                ORDER BY table, name
            """)
            
            return {
                'database': db_info[0] if db_info else None,
                'tables': tables_info,
                'indexes': indexes_info,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            return {'error': str(e)}
    
    def __del__(self):
        """Cleanup client connection."""
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass


class SampleDataGenerator:
    """
    Generate sample NSE data for testing and development.
    
    Creates realistic financial data following NSE patterns
    and market behavior for development and testing purposes.
    """
    
    def __init__(self, schema_manager: SchemaManager):
        """
        Initialize sample data generator.
        
        Args:
            schema_manager: Schema manager instance
        """
        self.schema_manager = schema_manager
        self.client = schema_manager._get_client()
        self.database = schema_manager.database
    
    def generate_nse_symbols(self) -> List[Dict[str, Any]]:
        """
        Generate sample NSE symbol master data.
        
        Returns:
            List of symbol dictionaries
        """
        symbols = [
            {
                'symbol': 'RELIANCE',
                'company_name': 'Reliance Industries Limited',
                'isin': 'INE002A01018',
                'sector': 'Energy',
                'industry': 'Oil & Gas',
                'market_cap': 1500000000000,  # 15 trillion
                'face_value': 10.0,
                'upper_circuit': 2750.0,
                'lower_circuit': 2250.0
            },
            {
                'symbol': 'TCS',
                'company_name': 'Tata Consultancy Services Limited',
                'isin': 'INE467B01029',
                'sector': 'Information Technology',
                'industry': 'IT Services',
                'market_cap': 1300000000000,  # 13 trillion
                'face_value': 1.0,
                'upper_circuit': 3850.0,
                'lower_circuit': 3150.0
            },
            {
                'symbol': 'INFY',
                'company_name': 'Infosys Limited',
                'isin': 'INE009A01021',
                'sector': 'Information Technology',
                'industry': 'IT Services',
                'market_cap': 750000000000,  # 7.5 trillion
                'face_value': 5.0,
                'upper_circuit': 1650.0,
                'lower_circuit': 1350.0
            },
            {
                'symbol': 'HDFCBANK',
                'company_name': 'HDFC Bank Limited',
                'isin': 'INE040A01034',
                'sector': 'Financial Services',
                'industry': 'Banking',
                'market_cap': 900000000000,  # 9 trillion
                'face_value': 1.0,
                'upper_circuit': 1650.0,
                'lower_circuit': 1350.0
            },
            {
                'symbol': 'ICICIBANK',
                'company_name': 'ICICI Bank Limited',
                'isin': 'INE090A01021',
                'sector': 'Financial Services',
                'industry': 'Banking',
                'market_cap': 650000000000,  # 6.5 trillion
                'face_value': 2.0,
                'upper_circuit': 1050.0,
                'lower_circuit': 850.0
            }
        ]
        return symbols
    
    def generate_tick_data(self, symbol: str, base_price: float, 
                          start_time: datetime, count: int = 1000) -> List[tuple]:
        """
        Generate realistic tick data for a symbol.
        
        Args:
            symbol: Trading symbol
            base_price: Starting price
            start_time: Start timestamp
            count: Number of ticks to generate
            
        Returns:
            List of tick tuples
        """
        ticks = []
        current_price = base_price
        current_time = start_time
        
        for i in range(count):
            # Realistic price movement (small random walk)
            price_change_pct = random.uniform(-0.002, 0.002)  # ±0.2% max change
            current_price *= (1 + price_change_pct)
            current_price = round(current_price, 2)
            
            # Random volume (realistic distribution)
            volume = random.randint(100, 10000)
            
            # Bid-ask spread (typically 0.05-0.10% of price)
            spread = current_price * random.uniform(0.0005, 0.001)
            bid_price = round(current_price - spread/2, 2)
            ask_price = round(current_price + spread/2, 2)
            
            tick = (
                symbol,
                current_time,
                current_price,
                volume,
                bid_price,
                ask_price,
                random.randint(50, 500),   # bid_size
                random.randint(50, 500),   # ask_size
                'NSE',
                'SAMPLE_DATA',
                f'T{i+1:06d}',  # trade_id
                1,  # trade_type = TRADE
            )
            
            ticks.append(tick)
            
            # Increment time by 1-5 seconds randomly
            current_time += timedelta(seconds=random.randint(1, 5))
            
        return ticks
    
    def insert_sample_data(self) -> bool:
        """
        Insert comprehensive sample data for testing.
        
        Returns:
            True if successful
        """
        try:
            logger.info("Inserting sample NSE data...")
            
            # Insert symbol master data
            symbols = self.generate_nse_symbols()
            
            # Use the existing reference data SQL instead of manual insertion
            # This ensures consistency with the schema
            ref_data_file = self.schema_manager.sql_dir / "04_insert_reference_data.sql"
            if ref_data_file.exists():
                self.schema_manager.execute_sql_file(ref_data_file)
                logger.info("Reference data inserted successfully")
            
            # Generate and insert sample tick data
            symbols_prices = {
                'RELIANCE': 2500.0,
                'TCS': 3500.0,
                'INFY': 1500.0,
                'HDFCBANK': 1500.0,
                'ICICIBANK': 950.0
            }
            
            # Generate data for the last hour
            start_time = datetime.utcnow() - timedelta(hours=1)
            
            for symbol, base_price in symbols_prices.items():
                ticks = self.generate_tick_data(symbol, base_price, start_time, 500)
                
                # Insert in batches for better performance
                batch_size = 100
                for i in range(0, len(ticks), batch_size):
                    batch = ticks[i:i + batch_size]
                    
                    self.client.execute(f"""
                        INSERT INTO {self.database}.raw_ticks 
                        (symbol, timestamp, price, volume, bid_price, ask_price, 
                         bid_size, ask_size, exchange, source, trade_id, trade_type)
                        VALUES
                    """, batch)
                
                logger.info(f"Inserted {len(ticks)} sample ticks for {symbol}")
            
            logger.info("✅ Sample data insertion completed!")
            return True
            
        except Exception as e:
            logger.error(f"Sample data insertion failed: {e}")
            return False


def main():
    """Main schema initialization function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize schema manager
        schema_manager = SchemaManager()
        
        # Initialize schema
        success = schema_manager.initialize_schema()
        
        if success:
            # Generate sample data for development
            generator = SampleDataGenerator(schema_manager)
            generator.insert_sample_data()
            
            logger.info("🎉 ClickHouse schema setup completed successfully!")
        else:
            logger.error("❌ Schema initialization failed")
            
    except Exception as e:
        logger.error(f"Main execution failed: {e}")


if __name__ == "__main__":
    main()