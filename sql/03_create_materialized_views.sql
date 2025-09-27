-- ClickHouse Materialized Views for NSE Data ETL Pipeline
-- Real-time aggregation views for high-frequency financial data
-- Optimized for streaming inserts and live analytics

USE nse_data;

-- Helper functions for time-based aggregations
-- Custom function for 5-minute intervals
CREATE FUNCTION IF NOT EXISTS toStartOfFiveMinute AS (dt) -> 
    toStartOfMinute(dt) - INTERVAL (toMinute(dt) % 5) MINUTE;

-- Custom function for 15-minute intervals  
CREATE FUNCTION IF NOT EXISTS toStartOfFifteenMinute AS (dt) ->
    toStartOfMinute(dt) - INTERVAL (toMinute(dt) % 15) MINUTE;

-- Custom function for 30-minute intervals
CREATE FUNCTION IF NOT EXISTS toStartOfThirtyMinute AS (dt) ->
    toStartOfMinute(dt) - INTERVAL (toMinute(dt) % 30) MINUTE;

-- 1. Real-Time 1-Minute OHLCV Materialized View
-- Automatically aggregates raw ticks into 1-minute bars
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_1m_mv TO ohlcv_bars AS
SELECT
    symbol,
    1 as timeframe,  -- 1m
    toStartOfMinute(timestamp) as timestamp,
    
    -- OHLCV calculations with proper ordering
    argMin(price, timestamp) as open,         -- First price in the minute
    max(price) as high,                       -- Highest price
    min(price) as low,                        -- Lowest price  
    argMax(price, timestamp) as close,        -- Last price in the minute
    sum(volume) as volume,                    -- Total volume
    
    -- Additional metrics
    count() as trade_count,                   -- Number of trades
    sum(price * volume) / sum(volume) as vwap, -- Volume Weighted Average Price
    sum(price * volume) as turnover,          -- Total turnover
    
    -- Time tracking
    min(timestamp) as first_trade_time,       -- First trade timestamp
    max(timestamp) as last_trade_time,        -- Last trade timestamp
    
    -- ETL metadata
    now() as inserted_at,
    now() as updated_at
FROM raw_ticks 
WHERE volume > 0 AND price > 0              -- Filter invalid data
GROUP BY symbol, toStartOfMinute(timestamp);

-- 2. Real-Time 5-Minute OHLCV Materialized View
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_5m_mv TO ohlcv_bars AS
SELECT
    symbol,
    5 as timeframe,  -- 5m
    toStartOfFiveMinute(timestamp) as timestamp,
    
    -- OHLCV calculations
    argMin(price, timestamp) as open,
    max(price) as high,
    min(price) as low,
    argMax(price, timestamp) as close,
    sum(volume) as volume,
    
    -- Additional metrics
    count() as trade_count,
    sum(price * volume) / sum(volume) as vwap,
    sum(price * volume) as turnover,
    
    -- Time tracking
    min(timestamp) as first_trade_time,
    max(timestamp) as last_trade_time,
    
    -- ETL metadata
    now() as inserted_at,
    now() as updated_at
FROM raw_ticks
WHERE volume > 0 AND price > 0
GROUP BY symbol, toStartOfFiveMinute(timestamp);

-- 3. Real-Time 15-Minute OHLCV Materialized View
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_15m_mv TO ohlcv_bars AS
SELECT
    symbol,
    15 as timeframe,  -- 15m
    toStartOfFifteenMinute(timestamp) as timestamp,
    
    -- OHLCV calculations
    argMin(price, timestamp) as open,
    max(price) as high,
    min(price) as low,
    argMax(price, timestamp) as close,
    sum(volume) as volume,
    
    -- Additional metrics
    count() as trade_count,
    sum(price * volume) / sum(volume) as vwap,
    sum(price * volume) as turnover,
    
    -- Time tracking
    min(timestamp) as first_trade_time,
    max(timestamp) as last_trade_time,
    
    -- ETL metadata
    now() as inserted_at,
    now() as updated_at
FROM raw_ticks
WHERE volume > 0 AND price > 0
GROUP BY symbol, toStartOfFifteenMinute(timestamp);

-- 4. Real-Time 1-Hour OHLCV Materialized View
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_1h_mv TO ohlcv_bars AS
SELECT
    symbol,
    60 as timeframe,  -- 1h
    toStartOfHour(timestamp) as timestamp,
    
    -- OHLCV calculations
    argMin(price, timestamp) as open,
    max(price) as high,
    min(price) as low,
    argMax(price, timestamp) as close,
    sum(volume) as volume,
    
    -- Additional metrics
    count() as trade_count,
    sum(price * volume) / sum(volume) as vwap,
    sum(price * volume) as turnover,
    
    -- Time tracking
    min(timestamp) as first_trade_time,
    max(timestamp) as last_trade_time,
    
    -- ETL metadata
    now() as inserted_at,
    now() as updated_at
FROM raw_ticks
WHERE volume > 0 AND price > 0
GROUP BY symbol, toStartOfHour(timestamp);

-- 5. Daily Summary Materialized View
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_daily_mv TO ohlcv_bars AS
SELECT
    symbol,
    1440 as timeframe,  -- 1d (1440 minutes)
    toDate(timestamp) as timestamp,
    
    -- OHLCV calculations
    argMin(price, timestamp) as open,
    max(price) as high,
    min(price) as low,
    argMax(price, timestamp) as close,
    sum(volume) as volume,
    
    -- Additional metrics
    count() as trade_count,
    sum(price * volume) / sum(volume) as vwap,
    sum(price * volume) as turnover,
    
    -- Time tracking
    min(timestamp) as first_trade_time,
    max(timestamp) as last_trade_time,
    
    -- ETL metadata
    now() as inserted_at,
    now() as updated_at
FROM raw_ticks
WHERE volume > 0 AND price > 0
GROUP BY symbol, toDate(timestamp);

-- 6. Real-Time Data Quality Monitoring View
-- Automatically tracks data quality metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS data_quality_live_mv TO data_quality_metrics AS
SELECT
    toDate(timestamp) as date,
    symbol,
    
    -- Tick counts
    count() as total_ticks,
    countIf(price > 0 AND volume > 0) as valid_ticks,
    countIf(price <= 0 OR volume <= 0) as invalid_ticks,
    0 as duplicate_ticks,  -- Will be calculated separately
    
    -- Data completeness analysis
    -- Count missing minutes (assuming 1-minute resolution)
    greatest(0, 
        dateDiff('minute', 
            toDateTime(toDate(timestamp) + INTERVAL 9 HOUR + INTERVAL 15 MINUTE), -- Market start 9:15 AM
            toDateTime(toDate(timestamp) + INTERVAL 15 HOUR + INTERVAL 30 MINUTE)  -- Market end 3:30 PM
        ) + 1 - uniq(toStartOfMinute(timestamp))
    ) as missing_minutes,
    
    -- Anomaly detection (simple statistical approach)
    countIf(abs(price - avg(price)) > 3 * stddevPop(price)) as price_anomalies,
    countIf(volume > avg(volume) + 5 * stddevPop(volume)) as volume_anomalies,
    
    -- Quality percentages
    countIf(price > 0 AND volume > 0) * 100.0 / count() as data_completeness_pct,
    countIf(
        price > 0 AND volume > 0 AND 
        abs(price - lag(price) OVER (PARTITION BY symbol ORDER BY timestamp)) / lag(price) OVER (PARTITION BY symbol ORDER BY timestamp) < 0.2
    ) * 100.0 / count() as data_accuracy_pct,
    
    -- Time boundaries
    min(timestamp) as first_tick_time,
    max(timestamp) as last_tick_time,
    
    -- ETL metadata
    now() as created_at
FROM raw_ticks
WHERE toDate(timestamp) = today()  -- Only process today's data
GROUP BY toDate(timestamp), symbol;

-- 7. Market Movers Real-Time View
-- Pre-compute top gainers/losers for fast API responses
CREATE MATERIALIZED VIEW IF NOT EXISTS market_movers_live_mv TO market_movers AS
WITH daily_changes AS (
    SELECT 
        toDate(timestamp) as date,
        symbol,
        argMin(price, timestamp) as open_price,
        argMax(price, timestamp) as close_price,
        sum(volume) as total_volume,
        sum(price * volume) as total_turnover,
        (argMax(price, timestamp) - argMin(price, timestamp)) / argMin(price, timestamp) * 100 as change_pct
    FROM raw_ticks 
    WHERE toDate(timestamp) = today()
    GROUP BY toDate(timestamp), symbol
    HAVING total_volume > 0 AND open_price > 0
),
ranked_changes AS (
    SELECT 
        *,
        row_number() OVER (ORDER BY change_pct DESC) as gain_rank,
        row_number() OVER (ORDER BY change_pct ASC) as loss_rank,
        row_number() OVER (ORDER BY total_volume DESC) as volume_rank,
        row_number() OVER (ORDER BY total_turnover DESC) as value_rank
    FROM daily_changes
)
-- Top gainers
SELECT date, 1 as timeframe, 1 as category, symbol, close_price as price, 
       change_pct, total_volume as volume, total_turnover as turnover, 
       gain_rank as rank, now() as updated_at
FROM ranked_changes WHERE gain_rank <= 50

UNION ALL

-- Top losers  
SELECT date, 1 as timeframe, 2 as category, symbol, close_price as price,
       change_pct, total_volume as volume, total_turnover as turnover,
       loss_rank as rank, now() as updated_at  
FROM ranked_changes WHERE loss_rank <= 50

UNION ALL

-- Most active by volume
SELECT date, 1 as timeframe, 3 as category, symbol, close_price as price,
       change_pct, total_volume as volume, total_turnover as turnover,
       volume_rank as rank, now() as updated_at
FROM ranked_changes WHERE volume_rank <= 50

UNION ALL

-- Most active by value
SELECT date, 1 as timeframe, 4 as category, symbol, close_price as price,
       change_pct, total_volume as volume, total_turnover as turnover,
       value_rank as rank, now() as updated_at
FROM ranked_changes WHERE value_rank <= 50;

-- 8. Symbol Statistics Real-Time View
-- Pre-calculate technical indicators and statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS symbol_stats_live_mv TO symbol_statistics AS
SELECT
    symbol,
    toDate(timestamp) as date,
    
    -- Basic statistics
    avg(price) as avg_price,
    stddevPop(price) as volatility,
    0.0 as beta,  -- Will be calculated separately with market index
    avg(volume) as avg_volume,
    avg(price * volume) as avg_turnover,
    
    -- Trading activity
    uniq(toStartOfMinute(timestamp)) as trading_sessions,
    max(price) as price_range_high,
    min(price) as price_range_low,
    
    -- Technical levels (simplified)
    quantile(0.2)(price) as support_level,
    quantile(0.8)(price) as resistance_level,
    
    -- Simple RSI calculation (14-period approximation)
    0.0 as rsi,  -- Will be calculated separately
    
    -- Moving averages (approximated for real-time)
    avg(price) as sma_20,  -- Simplified to daily average
    avgWeighted(price, volume) as ema_20,  -- Volume-weighted approximation
    
    -- ETL metadata
    now() as updated_at
FROM raw_ticks
WHERE toDate(timestamp) = today()
GROUP BY symbol, toDate(timestamp);

-- Performance optimization notes:
-- 1. All materialized views use filtered data (volume > 0, price > 0)
-- 2. Views are partitioned by date for efficient querying
-- 3. argMin/argMax functions ensure proper OHLC ordering
-- 4. Time functions use built-in ClickHouse optimizations
-- 5. Complex calculations are simplified for real-time performance

-- Monitoring materialized views:
-- SELECT * FROM system.tables WHERE database = 'nse_data' AND engine = 'MaterializedView';
-- SELECT * FROM system.mutations WHERE database = 'nse_data';

-- Performance tuning:
-- 1. Monitor view refresh rates with system.part_log
-- 2. Adjust aggregation intervals based on data volume
-- 3. Consider using POPULATE for historical data
-- 4. Use DETACH/ATTACH for maintenance operations