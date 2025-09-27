-- ClickHouse Schema for NSE Data ETL Pipeline
-- High-performance financial data storage with proper partitioning and indexing
-- Optimized for 1M+ inserts per second and efficient querying

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS nse_data;
USE nse_data;

-- 1. Raw Ticks Table - High Frequency Data
-- Optimized for massive insert volume with time-based partitioning
CREATE TABLE IF NOT EXISTS raw_ticks (
    symbol LowCardinality(String) COMMENT 'NSE symbol (e.g., RELIANCE, TCS)',
    timestamp DateTime64(3, 'UTC') COMMENT 'Trade timestamp in UTC with millisecond precision',
    price Float64 COMMENT 'Trade price with full precision',
    volume UInt64 COMMENT 'Trade volume/quantity',
    bid_price Nullable(Float64) COMMENT 'Best bid price at time of trade',
    ask_price Nullable(Float64) COMMENT 'Best ask price at time of trade',
    bid_size Nullable(UInt64) COMMENT 'Best bid quantity',
    ask_size Nullable(UInt64) COMMENT 'Best ask quantity',
    exchange LowCardinality(String) DEFAULT 'NSE' COMMENT 'Exchange identifier',
    source LowCardinality(String) COMMENT 'Data source identifier',
    trade_id Nullable(String) COMMENT 'Unique trade identifier from exchange',
    trade_type Enum8(
        'TRADE'=1, 
        'BID'=2, 
        'ASK'=3, 
        'LAST'=4
    ) DEFAULT 'TRADE' COMMENT 'Type of market data event',
    inserted_at DateTime64(3, 'UTC') DEFAULT now64() COMMENT 'ETL insertion timestamp'
) ENGINE = MergeTree()
ORDER BY (symbol, toStartOfMinute(timestamp), timestamp)
PARTITION BY toYYYYMM(timestamp)
TTL timestamp + INTERVAL 1 YEAR
SETTINGS 
    index_granularity = 8192,
    ttl_only_drop_parts = 1
COMMENT 'High-frequency tick data with time-based partitioning for optimal performance';

-- 2. OHLCV Bars Table - Aggregated Data
-- Using ReplacingMergeTree for upsert capabilities
CREATE TABLE IF NOT EXISTS ohlcv_bars (
    symbol LowCardinality(String) COMMENT 'NSE symbol',
    timeframe Enum8(
        '1m'=1, 
        '5m'=5, 
        '15m'=15, 
        '30m'=30, 
        '1h'=60, 
        '4h'=240, 
        '1d'=1440, 
        '1w'=10080
    ) DEFAULT '1m' COMMENT 'Bar timeframe in minutes',
    timestamp DateTime('UTC') COMMENT 'Bar start timestamp',
    open Float64 COMMENT 'Opening price',
    high Float64 COMMENT 'Highest price',
    low Float64 COMMENT 'Lowest price',
    close Float64 COMMENT 'Closing price',
    volume UInt64 COMMENT 'Total volume',
    trade_count UInt32 COMMENT 'Number of trades',
    vwap Float64 COMMENT 'Volume Weighted Average Price',
    turnover Float64 COMMENT 'Total value traded (price * volume)',
    first_trade_time DateTime64(3, 'UTC') COMMENT 'First trade timestamp in the bar',
    last_trade_time DateTime64(3, 'UTC') COMMENT 'Last trade timestamp in the bar',
    inserted_at DateTime('UTC') DEFAULT now() COMMENT 'ETL insertion timestamp',
    updated_at DateTime('UTC') DEFAULT now() COMMENT 'Last update timestamp'
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (symbol, timeframe, timestamp)
PARTITION BY (timeframe, toYYYYMM(timestamp))
TTL timestamp + INTERVAL 5 YEAR
SETTINGS 
    index_granularity = 8192,
    ttl_only_drop_parts = 1
COMMENT 'OHLCV bars for multiple timeframes with upsert capability';

-- 3. Symbol Master Table - Reference Data
-- Static reference data for NSE symbols
CREATE TABLE IF NOT EXISTS symbol_master (
    symbol String COMMENT 'NSE trading symbol',
    company_name String COMMENT 'Full company name',
    isin String COMMENT 'International Securities Identification Number',
    sector LowCardinality(String) COMMENT 'Business sector',
    industry LowCardinality(String) COMMENT 'Industry classification',
    market_cap Nullable(UInt64) COMMENT 'Market capitalization in INR',
    face_value Nullable(Float64) COMMENT 'Face value of shares',
    listing_date Nullable(Date) COMMENT 'Date of listing on NSE',
    upper_circuit Nullable(Float64) COMMENT 'Upper circuit limit',
    lower_circuit Nullable(Float64) COMMENT 'Lower circuit limit',
    lot_size UInt32 DEFAULT 1 COMMENT 'Trading lot size',
    tick_size Float64 DEFAULT 0.01 COMMENT 'Minimum price movement',
    is_active Bool DEFAULT 1 COMMENT 'Whether symbol is actively traded',
    exchange LowCardinality(String) DEFAULT 'NSE' COMMENT 'Exchange identifier',
    created_at DateTime DEFAULT now() COMMENT 'Record creation timestamp',
    updated_at DateTime DEFAULT now() COMMENT 'Last update timestamp'
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY symbol
SETTINGS index_granularity = 8192
COMMENT 'Master data for NSE trading symbols';

-- 4. Market Events Table - Corporate Actions & News
-- Historical tracking of corporate actions and market events
CREATE TABLE IF NOT EXISTS market_events (
    id UInt64 COMMENT 'Unique event identifier',
    symbol String COMMENT 'Affected symbol',
    event_type Enum8(
        'DIVIDEND'=1, 
        'BONUS'=2, 
        'SPLIT'=3, 
        'RIGHTS'=4, 
        'MERGER'=5, 
        'DELISTING'=6, 
        'NEWS'=7,
        'RESULT'=8,
        'AGM'=9
    ) COMMENT 'Type of market event',
    event_date Date COMMENT 'Date when event occurs',
    ex_date Nullable(Date) COMMENT 'Ex-date for the event',
    record_date Nullable(Date) COMMENT 'Record date for eligibility',
    event_description String COMMENT 'Detailed description of the event',
    impact_factor Nullable(Float64) COMMENT 'Quantified impact (e.g., split ratio, dividend amount)',
    announcement_date Date COMMENT 'Date when event was announced',
    source LowCardinality(String) COMMENT 'Source of the information',
    created_at DateTime DEFAULT now() COMMENT 'Record creation timestamp'
) ENGINE = MergeTree()
ORDER BY (symbol, event_date, id)
PARTITION BY toYYYYMM(event_date)
TTL event_date + INTERVAL 10 YEAR
SETTINGS index_granularity = 8192
COMMENT 'Corporate actions and market events affecting symbols';

-- 5. Data Quality Metrics Table - Monitoring
-- Track data quality and completeness for monitoring
CREATE TABLE IF NOT EXISTS data_quality_metrics (
    date Date COMMENT 'Date of metrics',
    symbol String COMMENT 'Symbol being measured',
    total_ticks UInt64 COMMENT 'Total ticks received',
    valid_ticks UInt64 COMMENT 'Valid ticks after validation',
    invalid_ticks UInt64 COMMENT 'Invalid/rejected ticks',
    duplicate_ticks UInt64 COMMENT 'Duplicate ticks filtered',
    missing_minutes UInt16 COMMENT 'Number of minutes with no data',
    price_anomalies UInt32 COMMENT 'Price anomalies detected',
    volume_anomalies UInt32 COMMENT 'Volume anomalies detected',
    data_completeness_pct Float64 COMMENT 'Data completeness percentage',
    data_accuracy_pct Float64 COMMENT 'Data accuracy percentage',
    first_tick_time DateTime64(3, 'UTC') COMMENT 'First tick timestamp of the day',
    last_tick_time DateTime64(3, 'UTC') COMMENT 'Last tick timestamp of the day',
    created_at DateTime DEFAULT now() COMMENT 'Metrics calculation timestamp'
) ENGINE = MergeTree()
ORDER BY (date, symbol)
PARTITION BY toYYYYMM(date)
TTL date + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192
COMMENT 'Daily data quality metrics for monitoring and alerting';

-- 6. Market Movers Cache Table - Pre-computed Rankings
-- Pre-aggregated data for fast retrieval of top gainers/losers
CREATE TABLE IF NOT EXISTS market_movers (
    date Date COMMENT 'Trading date',
    timeframe Enum8('1d'=1, '1h'=2, '30m'=3, '15m'=4, '5m'=5) COMMENT 'Analysis timeframe',
    category Enum8(
        'GAINERS'=1, 
        'LOSERS'=2, 
        'ACTIVE'=3, 
        'HIGH_VALUE'=4,
        'HIGH_VOLUME'=5
    ) COMMENT 'Category of market movers',
    symbol String COMMENT 'Symbol',
    price Float64 COMMENT 'Current/closing price',
    change_pct Float64 COMMENT 'Percentage change',
    volume UInt64 COMMENT 'Total volume',
    turnover Float64 COMMENT 'Total turnover',
    rank UInt8 COMMENT 'Rank within category (1-50)',
    updated_at DateTime DEFAULT now() COMMENT 'Last update timestamp'
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (date, timeframe, category, rank)
PARTITION BY toYYYYMM(date)
TTL date + INTERVAL 3 MONTH
SETTINGS index_granularity = 8192
COMMENT 'Pre-computed market movers for fast API responses';

-- 7. Symbol Statistics Cache Table - Performance Metrics
-- Pre-calculated technical indicators and statistics
CREATE TABLE IF NOT EXISTS symbol_statistics (
    symbol String COMMENT 'Trading symbol',
    date Date COMMENT 'Calculation date',
    avg_price Float64 COMMENT 'Average price for the day',
    volatility Float64 COMMENT 'Price volatility (standard deviation of returns)',
    beta Float64 COMMENT 'Beta coefficient relative to market index',
    avg_volume UInt64 COMMENT 'Average volume',
    avg_turnover Float64 COMMENT 'Average turnover',
    trading_sessions UInt16 COMMENT 'Number of active trading sessions',
    price_range_high Float64 COMMENT 'Highest price in the period',
    price_range_low Float64 COMMENT 'Lowest price in the period',
    support_level Float64 COMMENT 'Calculated support level',
    resistance_level Float64 COMMENT 'Calculated resistance level',
    rsi Float64 COMMENT 'Relative Strength Index',
    sma_20 Float64 COMMENT '20-period Simple Moving Average',
    ema_20 Float64 COMMENT '20-period Exponential Moving Average',
    updated_at DateTime DEFAULT now() COMMENT 'Last calculation timestamp'
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (symbol, date)
PARTITION BY toYYYYMM(date)
TTL date + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192
COMMENT 'Pre-calculated technical indicators and symbol statistics';