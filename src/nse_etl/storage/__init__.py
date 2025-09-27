"""
Storage Module.

Handles data persistence to various storage systems including:
- ClickHouse for analytical queries with optimized schema
- Redis for caching and real-time data
- File system for backups
- Database connections, migrations, and schema management
- Performance benchmarking and monitoring
"""

try:
    from .base import BaseStorage
    from .clickhouse_storage import ClickHouseStorage
    from .redis_storage import RedisStorage
    from .file_storage import FileStorage
except ImportError:
    # Fallback for missing modules
    BaseStorage = None
    ClickHouseStorage = None
    RedisStorage = None
    FileStorage = None

# Schema management and data models
from .models import (
    RawTick, OHLCVBar, SymbolMaster, MarketEvent,
    DataQualityMetrics, MarketMover, SymbolStatistics,
    TradeType, Timeframe, EventType, MoverCategory,
    normalize_nse_symbol, validate_market_hours, calculate_percentage_change
)
from .schema_manager import SchemaManager, SampleDataGenerator
from .benchmark import ClickHouseBenchmark
from .cli import (
    init_schema, verify_schema, run_benchmark, 
    optimize_schema, generate_sample_data, export_schema
)

__all__ = [
    # Storage backends
    "BaseStorage",
    "ClickHouseStorage",
    "RedisStorage", 
    "FileStorage",
    
    # Data models
    "RawTick",
    "OHLCVBar", 
    "SymbolMaster",
    "MarketEvent",
    "DataQualityMetrics",
    "MarketMover",
    "SymbolStatistics",
    
    # Enums
    "TradeType",
    "Timeframe",
    "EventType", 
    "MoverCategory",
    
    # Utility functions
    "normalize_nse_symbol",
    "validate_market_hours",
    "calculate_percentage_change",
    
    # Schema management
    "SchemaManager",
    "SampleDataGenerator", 
    "ClickHouseBenchmark",
    
    # CLI functions
    "init_schema",
    "verify_schema",
    "run_benchmark",
    "optimize_schema",
    "generate_sample_data",
    "export_schema",
]