"""
Unit tests for ClickHouse schema implementation.

Tests data models, schema management, and validation logic
for the NSE data ETL pipeline.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, patch
import pytz

from nse_etl.storage.models import (
    RawTick, OHLCVBar, SymbolMaster, MarketEvent,
    TradeType, Timeframe, EventType,
    normalize_nse_symbol, validate_market_hours, calculate_percentage_change
)


class TestDataModels:
    """Test data model validation and functionality."""
    
    def test_raw_tick_validation(self):
        """Test RawTick model validation."""
        # Valid tick data
        tick = RawTick(
            symbol="RELIANCE",
            timestamp=datetime.now(pytz.UTC),
            price=Decimal("2500.50"),
            volume=1000,
            source="TEST"
        )
        
        assert tick.symbol == "RELIANCE"
        assert tick.price == Decimal("2500.50")
        assert tick.volume == 1000
        assert tick.trade_type == TradeType.TRADE
        
    def test_raw_tick_symbol_normalization(self):
        """Test symbol normalization in RawTick."""
        tick = RawTick(
            symbol="  reliance  ",
            timestamp=datetime.now(pytz.UTC),
            price=Decimal("2500.50"),
            volume=1000,
            source="TEST"
        )
        
        assert tick.symbol == "RELIANCE"
    
    def test_raw_tick_price_validation(self):
        """Test price validation in RawTick."""
        with pytest.raises(ValueError, match="Price must be positive"):
            RawTick(
                symbol="RELIANCE",
                timestamp=datetime.now(pytz.UTC),
                price=Decimal("-100.00"),
                volume=1000,
                source="TEST"
            )
    
    def test_ohlcv_bar_validation(self):
        """Test OHLCVBar model validation."""
        now = datetime.now(pytz.UTC)
        
        bar = OHLCVBar(
            symbol="TCS",
            timeframe=Timeframe.ONE_MINUTE,
            timestamp=now,
            open=Decimal("3500.00"),
            high=Decimal("3520.00"),
            low=Decimal("3490.00"),
            close=Decimal("3510.00"),
            volume=5000,
            trade_count=100,
            vwap=Decimal("3505.25"),
            turnover=Decimal("17526250.00"),
            first_trade_time=now,
            last_trade_time=now
        )
        
        assert bar.symbol == "TCS"
        assert bar.high >= bar.open
        assert bar.high >= bar.close
        assert bar.low <= bar.open
        assert bar.low <= bar.close
    
    def test_ohlcv_invalid_prices(self):
        """Test OHLCV validation with invalid price relationships."""
        now = datetime.now(pytz.UTC)
        
        with pytest.raises(ValueError, match="High price must be"):
            OHLCVBar(
                symbol="TCS",
                timeframe=Timeframe.ONE_MINUTE,
                timestamp=now,
                open=Decimal("3500.00"),
                high=Decimal("3400.00"),  # High < open
                low=Decimal("3490.00"),
                close=Decimal("3510.00"),
                volume=5000,
                trade_count=100,
                vwap=Decimal("3505.25"),
                turnover=Decimal("17526250.00"),
                first_trade_time=now,
                last_trade_time=now
            )
    
    def test_symbol_master_validation(self):
        """Test SymbolMaster model validation."""
        symbol = SymbolMaster(
            symbol="INFY",
            company_name="Infosys Limited",
            isin="INE009A01021",
            sector="Information Technology",
            industry="IT Services",
            market_cap=750000000000,
            face_value=Decimal("5.00"),
            upper_circuit=Decimal("1650.00"),
            lower_circuit=Decimal("1350.00")
        )
        
        assert symbol.symbol == "INFY"
        assert symbol.upper_circuit > symbol.lower_circuit
    
    def test_symbol_master_circuit_validation(self):
        """Test circuit limit validation."""
        with pytest.raises(ValueError, match="Upper circuit must be greater"):
            SymbolMaster(
                symbol="INFY",
                company_name="Infosys Limited",
                isin="INE009A01021",
                sector="Information Technology",  
                industry="IT Services",
                upper_circuit=Decimal("1300.00"),
                lower_circuit=Decimal("1400.00")  # Lower > Upper
            )
    
    def test_market_event_validation(self):
        """Test MarketEvent model validation."""
        event = MarketEvent(
            id=1,
            symbol="TCS",
            event_type=EventType.DIVIDEND,
            event_date=date.today(),
            event_description="Interim dividend of Rs 9 per share",
            impact_factor=Decimal("9.00"),
            announcement_date=date.today(),
            source="NSE"
        )
        
        assert event.event_type == EventType.DIVIDEND
        assert event.impact_factor == Decimal("9.00")


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_normalize_nse_symbol(self):
        """Test NSE symbol normalization."""
        assert normalize_nse_symbol("reliance") == "RELIANCE"
        assert normalize_nse_symbol("TCS-EQ") == "TCS"
        assert normalize_nse_symbol("  INFY  ") == "INFY"
        assert normalize_nse_symbol("") == ""
    
    def test_validate_market_hours(self):
        """Test market hours validation."""
        # Create IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        
        # Market hours: 9:15 AM - 3:30 PM IST
        market_open = datetime.now(ist).replace(hour=10, minute=0, second=0, microsecond=0)
        market_closed = datetime.now(ist).replace(hour=16, minute=0, second=0, microsecond=0)
        
        assert validate_market_hours(market_open) == True
        assert validate_market_hours(market_closed) == False
    
    def test_calculate_percentage_change(self):
        """Test percentage change calculations."""
        old_price = Decimal("100.00")
        new_price = Decimal("110.00")
        
        change = calculate_percentage_change(old_price, new_price)
        assert change == Decimal("10.00")
        
        # Test zero old price
        zero_change = calculate_percentage_change(Decimal("0"), new_price)
        assert zero_change == Decimal("0")


class TestSchemaManager:
    """Test schema manager functionality."""
    
    @patch('nse_etl.storage.schema_manager.Client')
    def test_schema_manager_init(self, mock_client_class):
        """Test SchemaManager initialization."""
        from nse_etl.storage.schema_manager import SchemaManager
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        schema_manager = SchemaManager()
        
        assert schema_manager.database == "nse_data"
        assert len(schema_manager.schema_files) == 4
    
    @patch('nse_etl.storage.schema_manager.Client')
    def test_create_database(self, mock_client_class):
        """Test database creation."""
        from nse_etl.storage.schema_manager import SchemaManager
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        schema_manager = SchemaManager()
        schema_manager.create_database()
        
        mock_client.execute.assert_called_once()
        call_args = mock_client.execute.call_args[0][0]
        assert "CREATE DATABASE IF NOT EXISTS" in call_args
    
    @patch('nse_etl.storage.schema_manager.Client')
    def test_verify_tables(self, mock_client_class):
        """Test table verification."""
        from nse_etl.storage.schema_manager import SchemaManager
        
        mock_client = Mock()
        mock_client.execute.return_value = [[1]]  # Table exists
        mock_client_class.return_value = mock_client
        
        schema_manager = SchemaManager()
        results = schema_manager.verify_tables()
        
        assert 'raw_ticks' in results
        assert 'ohlcv_bars' in results
        assert all(results.values())  # All tables should exist in mock


class TestSampleDataGenerator:
    """Test sample data generation."""
    
    @patch('nse_etl.storage.schema_manager.Client')
    def test_generate_nse_symbols(self, mock_client_class):
        """Test NSE symbol generation."""
        from nse_etl.storage.schema_manager import SampleDataGenerator, SchemaManager
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        schema_manager = SchemaManager()
        generator = SampleDataGenerator(schema_manager)
        
        symbols = generator.generate_nse_symbols()
        
        assert len(symbols) >= 5
        assert any(s['symbol'] == 'RELIANCE' for s in symbols)
        assert any(s['symbol'] == 'TCS' for s in symbols)
    
    @patch('nse_etl.storage.schema_manager.Client')
    def test_generate_tick_data(self, mock_client_class):
        """Test tick data generation."""
        from nse_etl.storage.schema_manager import SampleDataGenerator, SchemaManager
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        schema_manager = SchemaManager()
        generator = SampleDataGenerator(schema_manager)
        
        ticks = generator.generate_tick_data(
            symbol="TEST",
            base_price=1000.0,
            start_time=datetime.utcnow(),
            count=100
        )
        
        assert len(ticks) == 100
        assert all(len(tick) == 12 for tick in ticks)  # 12 fields per tick
        assert all(tick[0] == "TEST" for tick in ticks)  # Symbol field


class TestCLIFunctions:
    """Test CLI functions."""
    
    @patch('nse_etl.storage.cli.SchemaManager')
    def test_init_schema_function(self, mock_schema_manager_class):
        """Test schema initialization function."""
        from nse_etl.storage.cli import init_schema
        
        mock_schema_manager = Mock()
        mock_schema_manager.initialize_schema.return_value = True
        mock_schema_manager_class.return_value = mock_schema_manager
        
        result = init_schema(confirm=True, with_sample_data=False)
        
        assert result == True
        mock_schema_manager.initialize_schema.assert_called_once()
    
    @patch('nse_etl.storage.cli.SchemaManager')
    def test_verify_schema_function(self, mock_schema_manager_class):
        """Test schema verification function."""
        from nse_etl.storage.cli import verify_schema
        
        mock_schema_manager = Mock()
        mock_schema_manager.verify_tables.return_value = {
            'raw_ticks': True,
            'ohlcv_bars': True
        }
        mock_schema_manager.verify_materialized_views.return_value = {
            'ohlcv_1m_mv': True
        }
        mock_schema_manager_class.return_value = mock_schema_manager
        
        result = verify_schema()
        
        assert result == True
        mock_schema_manager.verify_tables.assert_called_once()
        mock_schema_manager.verify_materialized_views.assert_called_once()


@pytest.mark.integration
class TestSchemaIntegration:
    """Integration tests for schema (requires actual ClickHouse)."""
    
    def test_schema_sql_files_exist(self):
        """Test that all required SQL files exist."""
        from pathlib import Path
        
        sql_dir = Path(__file__).parent.parent.parent / "sql"
        required_files = [
            "01_create_tables.sql",
            "02_create_indexes.sql",
            "03_create_materialized_views.sql", 
            "04_insert_reference_data.sql"
        ]
        
        for sql_file in required_files:
            file_path = sql_dir / sql_file
            assert file_path.exists(), f"Required SQL file not found: {sql_file}"
            
            # Check file is not empty
            content = file_path.read_text()
            assert len(content.strip()) > 0, f"SQL file is empty: {sql_file}"
    
    def test_sql_syntax_basic(self):
        """Basic SQL syntax validation."""
        from pathlib import Path
        
        sql_dir = Path(__file__).parent.parent.parent / "sql"
        
        for sql_file in sql_dir.glob("*.sql"):
            content = sql_file.read_text()
            
            # Basic syntax checks
            assert content.count('(') == content.count(')'), f"Unmatched parentheses in {sql_file.name}"
            assert 'CREATE TABLE' in content or 'CREATE MATERIALIZED VIEW' in content or 'INSERT INTO' in content, \
                f"No CREATE or INSERT statements found in {sql_file.name}"


if __name__ == "__main__":
    pytest.main([__file__])