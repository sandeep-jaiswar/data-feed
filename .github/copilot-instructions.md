# GitHub Copilot Instructions for NSE Data ETL Pipeline

## Project Overview

This is a **production-grade NSE (National Stock Exchange) data ETL pipeline** designed for **high-frequency financial data processing**. The system ingests real-time market data from NSE public APIs and WebSocket feeds, processes it with sub-second latency, and stores it in ClickHouse for analytics.

**Domain**: Financial Technology / Quantitative Trading  
**Scale**: 10,000+ ticks per second, millions of records per day  
**Standards**: Investment banking grade reliability and performance

## Architecture & Technology Stack

### Core Technologies
- **Language**: Python 3.9+ with full async/await support
- **Database**: ClickHouse (optimized for time-series financial data)
- **Web Framework**: aiohttp for async HTTP clients
- **WebSocket**: websockets library for real-time data streams
- **Data Processing**: Pandas, NumPy for financial calculations
- **Orchestration**: Apache Airflow for pipeline management
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker + Kubernetes

### Key Design Patterns
1. **Async-First Architecture**: All I/O operations must be asynchronous
2. **Producer-Consumer Pattern**: Queue-based data flow with backpressure handling
3. **Circuit Breaker Pattern**: Graceful degradation during API failures
4. **Event-Driven Architecture**: Real-time processing with event streams
5. **Repository Pattern**: Clean data access layer abstraction

## Code Style & Standards

### Python Conventions
```python
# Use type hints for all functions and methods
async def process_tick(self, tick: ProcessedTick) -> OHLCVBar:
    """Process a single tick into OHLCV format."""
    pass

# Use dataclasses for data models
@dataclass
class ProcessedTick:
    symbol: str
    timestamp: datetime
    price: float
    volume: int

# Use Pydantic for configuration and validation
class DatabaseConfig(BaseSettings):
    host: str
    port: int = 9000
    database: str
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `NSEAPIClient`, `TickProcessor`)
- **Functions/Methods**: snake_case (e.g., `process_tick`, `get_market_data`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`, `MAX_RETRIES`)
- **Private Members**: Single underscore prefix (e.g., `_validate_data`)
- **Database Tables**: snake_case (e.g., `raw_ticks`, `ohlcv_bars`)

### Error Handling Patterns
```python
# Custom exceptions for different error types
class NSEAPIError(Exception):
    """NSE API related errors"""
    pass

class DataValidationError(Exception):
    """Data validation failures"""
    pass

# Comprehensive error handling with logging
async def fetch_quote(self, symbol: str) -> QuoteResponse:
    try:
        async with self.session.get(url) as response:
            if response.status == 200:
                return await self._parse_response(response)
            else:
                raise NSEAPIError(f"API error: {response.status}")
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching {symbol}: {e}")
        raise NSEAPIError(f"Network error: {e}") from e
    except Exception as e:
        logger.exception(f"Unexpected error fetching {symbol}")
        raise
```

## Financial Domain Patterns

### Data Models
```python
# Time-series data should always include timezone
@dataclass
class MarketTick:
    symbol: str
    timestamp: datetime  # Always UTC timezone
    price: Decimal  # Use Decimal for financial precision
    volume: int
    bid_price: Optional[Decimal] = None
    ask_price: Optional[Decimal] = None

# OHLCV bars for different timeframes
@dataclass  
class OHLCVBar:
    symbol: str
    timeframe: Literal['1m', '5m', '15m', '1h', '1d']
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    trade_count: int
```

### Financial Calculations
```python
# Always validate financial data ranges
def validate_price(price: float, symbol: str) -> bool:
    """Validate price is within reasonable bounds"""
    if price <= 0:
        return False
    # Check circuit limits, historical ranges, etc.
    return True

# Use appropriate precision for financial calculations
def calculate_percentage_change(old_price: Decimal, new_price: Decimal) -> Decimal:
    """Calculate percentage change with proper precision"""
    if old_price == 0:
        return Decimal('0')
    return ((new_price - old_price) / old_price) * Decimal('100')
```

### NSE-Specific Patterns
```python
# NSE symbol normalization
def normalize_nse_symbol(symbol: str) -> str:
    """Standardize NSE symbol format"""
    return symbol.upper().strip().replace('-EQ', '')

# NSE market hours validation
def is_market_open() -> bool:
    """Check if NSE market is currently open"""
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    # Market hours: 9:15 AM - 3:30 PM IST
    market_open = now.replace(hour=9, minute=15, second=0)
    market_close = now.replace(hour=15, minute=30, second=0)
    return market_open <= now <= market_close
```

## Performance Requirements

### High-Frequency Data Processing
```python
# Batch processing for high throughput
async def process_tick_batch(self, ticks: List[RawTick]) -> List[ProcessedTick]:
    """Process ticks in batches for optimal performance"""
    # Target: 10,000+ ticks per second
    # Use vectorized operations when possible
    processed = []
    for batch in chunk_list(ticks, batch_size=1000):
        batch_result = await self._process_batch_vectorized(batch)
        processed.extend(batch_result)
    return processed

# Memory-efficient data structures
class SlidingWindow:
    """Memory-efficient sliding window for OHLCV calculation"""
    def __init__(self, window_size: int):
        self.data = deque(maxlen=window_size)  # Automatic memory management
        
# Async context managers for resource management
async def get_database_connection(self):
    """Get database connection from pool"""
    async with self.connection_pool.acquire() as conn:
        yield conn
        # Connection automatically returned to pool
```

### Caching Strategies
```python
# Cache frequently accessed data
from cachetools import TTLCache

class MarketDataCache:
    def __init__(self):
        self.cache = TTLCache(maxsize=10000, ttl=60)  # 1-minute TTL
    
    async def get_latest_price(self, symbol: str) -> Optional[float]:
        if symbol in self.cache:
            return self.cache[symbol]
        
        # Fetch from database if not cached
        price = await self.db.get_latest_price(symbol)
        self.cache[symbol] = price
        return price
```

## Database Patterns

### ClickHouse Optimizations
```python
# Batch inserts for optimal performance
async def insert_ticks_batch(self, ticks: List[ProcessedTick]) -> None:
    """Optimized batch insert for ClickHouse"""
    if len(ticks) < self.min_batch_size:
        return  # Wait for larger batch
    
    # Convert to ClickHouse-optimized format
    data = [
        (tick.symbol, tick.timestamp, tick.price, tick.volume)
        for tick in ticks
    ]
    
    query = """
    INSERT INTO raw_ticks (symbol, timestamp, price, volume) 
    VALUES
    """
    
    async with self.get_connection() as conn:
        await conn.execute(query, data)

# Use materialized views for real-time aggregations
CREATE_OHLCV_VIEW = """
CREATE MATERIALIZED VIEW ohlcv_1m_mv TO ohlcv_bars AS
SELECT
    symbol,
    toStartOfMinute(timestamp) as timestamp,
    argMin(price, timestamp) as open,
    max(price) as high,
    min(price) as low,
    argMax(price, timestamp) as close,
    sum(volume) as volume
FROM raw_ticks
GROUP BY symbol, toStartOfMinute(timestamp)
"""
```

### Data Partitioning
```python
# Time-based partitioning for financial data
def get_partition_key(timestamp: datetime) -> str:
    """Generate partition key for time-series data"""
    return timestamp.strftime('%Y%m')  # Monthly partitions

# Efficient queries with proper WHERE clauses
async def get_historical_data(
    self, 
    symbol: str, 
    start: datetime, 
    end: datetime
) -> pd.DataFrame:
    """Fetch historical data with optimized query"""
    query = """
    SELECT timestamp, open, high, low, close, volume
    FROM ohlcv_bars
    WHERE symbol = %(symbol)s
    AND timestamp BETWEEN %(start)s AND %(end)s
    ORDER BY timestamp
    """
    # ClickHouse will use partition pruning automatically
```

## Security Best Practices

### API Security
```python
# Secure API key management
class NSEConfig(BaseSettings):
    api_key: str = Field(..., env='NSE_API_KEY')  # From environment
    api_secret: str = Field(..., env='NSE_API_SECRET')
    
    class Config:
        env_file = '.env'
        case_sensitive = True

# Rate limiting to prevent abuse
from asyncio import Semaphore

class RateLimiter:
    def __init__(self, rate: int):
        self.semaphore = Semaphore(rate)
    
    async def acquire(self):
        await self.semaphore.acquire()
        # Release after delay
        await asyncio.sleep(1.0 / self.rate)
        self.semaphore.release()
```

### Data Validation
```python
# Validate all external data
def validate_market_data(data: dict) -> bool:
    """Validate incoming market data"""
    required_fields = ['symbol', 'price', 'timestamp', 'volume']
    
    # Check required fields
    if not all(field in data for field in required_fields):
        return False
    
    # Validate data types and ranges
    try:
        price = float(data['price'])
        volume = int(data['volume'])
        if price <= 0 or volume < 0:
            return False
    except (ValueError, TypeError):
        return False
    
    return True
```

## Testing Patterns

### Unit Testing
```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.mark.asyncio
async def test_tick_processor():
    """Test tick processing logic"""
    processor = TickProcessor()
    
    # Test data
    raw_tick = {
        'symbol': 'RELIANCE',
        'price': 2500.0,
        'volume': 100,
        'timestamp': datetime.now(UTC)
    }
    
    result = await processor.process_tick(raw_tick)
    
    assert result.symbol == 'RELIANCE'
    assert result.price == Decimal('2500.0')
    assert isinstance(result.timestamp, datetime)

# Mock external dependencies
@pytest.fixture
def mock_nse_client():
    client = Mock(spec=NSEClient)
    client.get_quote = AsyncMock(return_value=sample_quote_response())
    return client
```

### Integration Testing
```python
@pytest.mark.integration
async def test_end_to_end_pipeline():
    """Test complete data flow from API to database"""
    # Use test database
    db_config = get_test_db_config()
    
    # Create test pipeline
    pipeline = NSEDataPipeline(config=db_config)
    
    # Process test data
    test_symbols = ['NIFTY', 'BANKNIFTY']
    await pipeline.collect_and_process(test_symbols)
    
    # Verify data in database
    for symbol in test_symbols:
        data = await pipeline.db.get_latest_data(symbol)
        assert data is not None
        assert data.symbol == symbol
```

## Monitoring & Observability

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
ticks_processed = Counter('nse_ticks_processed_total', 'Total ticks processed')
processing_latency = Histogram('nse_processing_latency_seconds', 'Processing latency')
api_errors = Counter('nse_api_errors_total', 'API errors', ['error_type'])

# Use metrics in code
async def process_tick(self, tick: RawTick) -> ProcessedTick:
    start_time = time.time()
    try:
        result = await self._do_process_tick(tick)
        ticks_processed.inc()
        return result
    except Exception as e:
        api_errors.labels(error_type=type(e).__name__).inc()
        raise
    finally:
        processing_latency.observe(time.time() - start_time)
```

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

async def fetch_market_data(self, symbol: str) -> MarketData:
    """Fetch market data with structured logging"""
    logger.info("Fetching market data", symbol=symbol)
    
    try:
        data = await self.api_client.get_quote(symbol)
        logger.info(
            "Market data fetched successfully",
            symbol=symbol,
            price=data.price,
            volume=data.volume
        )
        return data
    except Exception as e:
        logger.error(
            "Failed to fetch market data",
            symbol=symbol,
            error=str(e),
            exc_info=True
        )
        raise
```

## Documentation Standards

### Function Documentation
```python
async def calculate_ohlcv(
    self, 
    ticks: List[ProcessedTick], 
    timeframe: str = '1m'
) -> OHLCVBar:
    """
    Calculate OHLCV bar from tick data.
    
    Args:
        ticks: List of processed tick data, must be sorted by timestamp
        timeframe: Bar timeframe ('1m', '5m', '15m', '1h', '1d')
        
    Returns:
        OHLCVBar: Aggregated OHLCV data for the timeframe
        
    Raises:
        ValueError: If ticks list is empty or timeframe is invalid
        DataValidationError: If tick data is inconsistent
        
    Example:
        >>> processor = OHLCVProcessor()
        >>> ticks = [tick1, tick2, tick3]  # ProcessedTick objects
        >>> bar = await processor.calculate_ohlcv(ticks, '5m')
        >>> assert bar.timeframe == '5m'
    """
```

### Class Documentation
```python
class NSEWebSocketClient:
    """
    NSE WebSocket client for real-time market data streaming.
    
    This client handles connection management, message parsing, and
    automatic reconnection for NSE WebSocket feeds. It supports
    symbol subscription/unsubscription and provides backpressure
    handling for high-frequency data streams.
    
    Attributes:
        connection_url: WebSocket endpoint URL
        subscribed_symbols: Set of currently subscribed symbols
        message_buffer: Queue for incoming messages
        
    Example:
        >>> client = NSEWebSocketClient(config)
        >>> await client.connect()
        >>> await client.subscribe(['NIFTY', 'BANKNIFTY'])
        >>> async for message in client.message_stream():
        ...     await process_message(message)
    """
```

## Common Pitfalls to Avoid

1. **Timezone Issues**: Always use UTC for internal processing, convert to IST only for display
2. **Floating Point Precision**: Use Decimal for financial calculations, not float
3. **Memory Leaks**: Properly close connections and clear caches
4. **Blocking I/O**: Never use synchronous I/O in async functions
5. **Race Conditions**: Use proper locking for shared resources
6. **API Rate Limits**: Implement proper backoff and retry strategies
7. **SQL Injection**: Use parameterized queries, never string concatenation

## File Organization

```
src/nse_etl/
├── config/          # Configuration and settings
├── collectors/      # Data collection from external sources
├── processors/      # Data transformation and validation
├── storage/         # Database access and models
├── monitoring/      # Health checks and metrics
└── utils/          # Shared utilities and helpers

tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests with external services
├── performance/    # Load and performance tests
└── fixtures/       # Test data and mocks
```

## Development Workflow

1. **Feature Development**: Create feature branch from `main`
2. **Code Quality**: All code must pass pre-commit hooks (black, flake8, mypy)
3. **Testing**: Minimum 90% test coverage required
4. **Documentation**: Update docstrings and README for public APIs
5. **Performance**: Include benchmarks for critical path code
6. **Security**: Security scan with bandit before merge
7. **Review**: Peer review focusing on financial logic and error handling

## Integration Points

When integrating with external systems:

1. **NSE APIs**: Handle rate limits, authentication, and data format changes
2. **ClickHouse**: Optimize for batch inserts and time-series queries  
3. **Airflow**: Create DAGs with proper error handling and monitoring
4. **Monitoring**: Export metrics to Prometheus, create Grafana dashboards
5. **Message Queues**: Use Redis for temporary buffering and coordination

Remember: This is financial data infrastructure. **Reliability, accuracy, and performance are critical**. When in doubt, choose the more robust, well-tested approach over clever optimizations.
