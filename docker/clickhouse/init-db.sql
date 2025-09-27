-- NSE Data ETL Database Initialization
-- Creates necessary databases and tables for financial data processing

-- Create main database
CREATE DATABASE IF NOT EXISTS nse_data;

-- Create test database
CREATE DATABASE IF NOT EXISTS nse_data_test;

-- Use main database
USE nse_data;

-- Equity data table with optimized structure for financial data
CREATE TABLE IF NOT EXISTS equity_data (
    symbol String,
    series String,
    date Date DEFAULT today(),
    timestamp DateTime64(3, 'Asia/Kolkata'),
    open Decimal64(4),
    high Decimal64(4),
    low Decimal64(4),
    close Decimal64(4),
    last Decimal64(4),
    prev_close Decimal64(4),
    total_traded_quantity UInt64,
    total_traded_value Decimal64(2),
    total_trades UInt32,
    isin String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (symbol, timestamp)
TTL date + INTERVAL 5 YEAR;

-- Derivatives data table
CREATE TABLE IF NOT EXISTS derivatives_data (
    symbol String,
    expiry_date Date,
    instrument_type String,
    strike_price Decimal64(4),
    option_type String,
    date Date DEFAULT today(),
    timestamp DateTime64(3, 'Asia/Kolkata'),
    open Decimal64(4),
    high Decimal64(4),
    low Decimal64(4),
    close Decimal64(4),
    last Decimal64(4),
    prev_close Decimal64(4),
    volume UInt64,
    value Decimal64(2),
    open_interest UInt64,
    change_in_oi Int64,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (symbol, expiry_date, instrument_type, timestamp)
TTL date + INTERVAL 5 YEAR;

-- Indices data table
CREATE TABLE IF NOT EXISTS indices_data (
    index_name String,
    date Date DEFAULT today(),
    timestamp DateTime64(3, 'Asia/Kolkata'),
    open Decimal64(4),
    high Decimal64(4),
    low Decimal64(4),
    close Decimal64(4),
    points_change Decimal64(4),
    percent_change Decimal64(4),
    volume UInt64,
    turnover Decimal64(2),
    pe Decimal64(4),
    pb Decimal64(4),
    div_yield Decimal64(4),
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (index_name, timestamp)
TTL date + INTERVAL 5 YEAR;

-- System metrics table for monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    metric_name String,
    metric_value Float64,
    labels Map(String, String),
    timestamp DateTime64(3, 'Asia/Kolkata') DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (metric_name, timestamp)
TTL timestamp + INTERVAL 90 DAY;

-- Processing logs table
CREATE TABLE IF NOT EXISTS processing_logs (
    log_level String,
    component String,
    message String,
    extra Map(String, String),
    timestamp DateTime64(3, 'Asia/Kolkata') DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY timestamp
TTL timestamp + INTERVAL 30 DAY;