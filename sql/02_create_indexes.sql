-- ClickHouse Indexes for NSE Data ETL Pipeline
-- Optimized indexes for high-frequency financial data queries
-- Performance-tuned for sub-second query response times

USE nse_data;

-- Indexes for raw_ticks table - High frequency data access patterns
-- MinMax indexes for efficient range queries on price and volume
ALTER TABLE raw_ticks ADD INDEX IF NOT EXISTS idx_timestamp_minmax timestamp TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for timestamp range queries';

ALTER TABLE raw_ticks ADD INDEX IF NOT EXISTS idx_price_minmax price TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for price range filtering';

ALTER TABLE raw_ticks ADD INDEX IF NOT EXISTS idx_volume_minmax volume TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for volume range filtering';

-- Bloom filter index for symbol filtering (high cardinality)
ALTER TABLE raw_ticks ADD INDEX IF NOT EXISTS idx_symbol_bloom symbol TYPE bloom_filter(0.01) GRANULARITY 1
COMMENT 'Bloom filter for efficient symbol filtering';

-- Set index for trade_type enum filtering
ALTER TABLE raw_ticks ADD INDEX IF NOT EXISTS idx_trade_type_set trade_type TYPE set(10) GRANULARITY 1
COMMENT 'Set index for trade type filtering';

-- Indexes for ohlcv_bars table - Aggregated data access patterns
ALTER TABLE ohlcv_bars ADD INDEX IF NOT EXISTS idx_close_minmax close TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for closing price range queries';

ALTER TABLE ohlcv_bars ADD INDEX IF NOT EXISTS idx_volume_minmax volume TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for volume-based filtering';

ALTER TABLE ohlcv_bars ADD INDEX IF NOT EXISTS idx_vwap_minmax vwap TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for VWAP filtering';

ALTER TABLE ohlcv_bars ADD INDEX IF NOT EXISTS idx_turnover_minmax turnover TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for turnover-based queries';

-- Set index for timeframe filtering
ALTER TABLE ohlcv_bars ADD INDEX IF NOT EXISTS idx_timeframe_set timeframe TYPE set(8) GRANULARITY 1
COMMENT 'Set index for timeframe filtering';

-- Indexes for symbol_master table - Reference data lookups
-- Bloom filter for symbol searches
ALTER TABLE symbol_master ADD INDEX IF NOT EXISTS idx_symbol_bloom symbol TYPE bloom_filter(0.001) GRANULARITY 1
COMMENT 'Bloom filter for symbol lookups';

-- Full-text search index for company names using tokenbf_v1
ALTER TABLE symbol_master ADD INDEX IF NOT EXISTS idx_company_name company_name TYPE tokenbf_v1(32768, 3, 0) GRANULARITY 1
COMMENT 'Full-text search index for company name searches';

-- Set indexes for categorical data
ALTER TABLE symbol_master ADD INDEX IF NOT EXISTS idx_sector_set sector TYPE set(100) GRANULARITY 1
COMMENT 'Set index for sector filtering';

ALTER TABLE symbol_master ADD INDEX IF NOT EXISTS idx_industry_set industry TYPE set(500) GRANULARITY 1
COMMENT 'Set index for industry filtering';

-- MinMax index for market cap filtering
ALTER TABLE symbol_master ADD INDEX IF NOT EXISTS idx_market_cap_minmax market_cap TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for market cap range filtering';

-- Indexes for market_events table - Event-based queries
ALTER TABLE market_events ADD INDEX IF NOT EXISTS idx_event_date_minmax event_date TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for event date range queries';

ALTER TABLE market_events ADD INDEX IF NOT EXISTS idx_event_type_set event_type TYPE set(10) GRANULARITY 1
COMMENT 'Set index for event type filtering';

ALTER TABLE market_events ADD INDEX IF NOT EXISTS idx_symbol_bloom symbol TYPE bloom_filter(0.01) GRANULARITY 1
COMMENT 'Bloom filter for symbol-based event queries';

-- Full-text index for event descriptions
ALTER TABLE market_events ADD INDEX IF NOT EXISTS idx_description_tokens event_description TYPE tokenbf_v1(32768, 3, 0) GRANULARITY 1
COMMENT 'Full-text search index for event description searches';

-- Indexes for data_quality_metrics table - Monitoring queries
ALTER TABLE data_quality_metrics ADD INDEX IF NOT EXISTS idx_date_minmax date TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for date range queries in monitoring';

ALTER TABLE data_quality_metrics ADD INDEX IF NOT EXISTS idx_completeness_minmax data_completeness_pct TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for data completeness filtering';

ALTER TABLE data_quality_metrics ADD INDEX IF NOT EXISTS idx_accuracy_minmax data_accuracy_pct TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for data accuracy filtering';

-- Indexes for market_movers table - Fast ranking queries
ALTER TABLE market_movers ADD INDEX IF NOT EXISTS idx_change_pct_minmax change_pct TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for percentage change filtering';

ALTER TABLE market_movers ADD INDEX IF NOT EXISTS idx_volume_minmax volume TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for volume-based filtering';

ALTER TABLE market_movers ADD INDEX IF NOT EXISTS idx_turnover_minmax turnover TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for turnover-based filtering';

-- Set indexes for categorical data
ALTER TABLE market_movers ADD INDEX IF NOT EXISTS idx_timeframe_set timeframe TYPE set(5) GRANULARITY 1
COMMENT 'Set index for timeframe filtering';

ALTER TABLE market_movers ADD INDEX IF NOT EXISTS idx_category_set category TYPE set(5) GRANULARITY 1
COMMENT 'Set index for category filtering';

-- Indexes for symbol_statistics table - Technical analysis queries
ALTER TABLE symbol_statistics ADD INDEX IF NOT EXISTS idx_volatility_minmax volatility TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for volatility-based filtering';

ALTER TABLE symbol_statistics ADD INDEX IF NOT EXISTS idx_beta_minmax beta TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for beta coefficient filtering';

ALTER TABLE symbol_statistics ADD INDEX IF NOT EXISTS idx_rsi_minmax rsi TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for RSI-based filtering';

ALTER TABLE symbol_statistics ADD INDEX IF NOT EXISTS idx_avg_volume_minmax avg_volume TYPE minmax GRANULARITY 1
COMMENT 'MinMax index for average volume filtering';

-- Advanced indexes for complex queries
-- Composite index for common time-series queries on raw_ticks
ALTER TABLE raw_ticks ADD INDEX IF NOT EXISTS idx_symbol_time_composite (symbol, toDate(timestamp)) TYPE minmax GRANULARITY 1
COMMENT 'Composite index for symbol and date-based queries';

-- Skip index for efficient TOP-K queries on ohlcv_bars
ALTER TABLE ohlcv_bars ADD INDEX IF NOT EXISTS idx_volume_skip volume TYPE minmax GRANULARITY 100
COMMENT 'Skip index for efficient volume-based TOP-K queries';

-- Performance optimization: Create skip indexes for large scans
ALTER TABLE raw_ticks ADD INDEX IF NOT EXISTS idx_price_skip price TYPE minmax GRANULARITY 1000
COMMENT 'Skip index for large price-based scans';

ALTER TABLE ohlcv_bars ADD INDEX IF NOT EXISTS idx_close_skip close TYPE minmax GRANULARITY 100
COMMENT 'Skip index for large closing price scans';

-- Specialized indexes for financial calculations
-- Index for intraday analysis on raw_ticks
ALTER TABLE raw_ticks ADD INDEX IF NOT EXISTS idx_hour_minute (toHour(timestamp), toMinute(timestamp)) TYPE set(1440) GRANULARITY 1
COMMENT 'Time-of-day index for intraday analysis';

-- Index for end-of-day analysis on ohlcv_bars  
ALTER TABLE ohlcv_bars ADD INDEX IF NOT EXISTS idx_daily_close (toDate(timestamp), close) TYPE minmax GRANULARITY 1
COMMENT 'Composite index for daily closing price analysis';

-- Bloom filter for trade_id lookups (when present)
ALTER TABLE raw_ticks ADD INDEX IF NOT EXISTS idx_trade_id_bloom trade_id TYPE bloom_filter(0.001) GRANULARITY 1
COMMENT 'Bloom filter for unique trade ID lookups';

-- Performance note: These indexes are optimized for:
-- 1. Time-range queries (common in financial analysis)
-- 2. Symbol-based filtering (portfolio analysis)
-- 3. Price/volume range queries (screening)
-- 4. Full-text search on company names and events
-- 5. Categorical filtering (sectors, industries, event types)
-- 6. Technical indicator calculations
-- 7. Market ranking and screening queries

-- Index usage guidelines:
-- - MinMax indexes: Best for range queries on numeric columns
-- - Bloom filters: Excellent for high-cardinality string columns
-- - Set indexes: Perfect for low-cardinality enum/categorical columns
-- - TokenBF: Ideal for full-text search capabilities
-- - Skip indexes: Useful for reducing data scanning in large tables

-- Monitor index effectiveness using:
-- SELECT * FROM system.data_skipping_indices WHERE database = 'nse_data';