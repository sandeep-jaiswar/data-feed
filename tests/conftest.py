"""
Pytest configuration and shared fixtures.

Provides common test fixtures and configuration for all test modules.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock

from nse_etl.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Provide test-specific settings."""
    return Settings(
        app_name="NSE Data ETL Test",
        environment="development",
        debug=True,
        secret_key="test-secret-key",
        log_level="DEBUG",
        database=Settings.DatabaseSettings(
            clickhouse_host="localhost",
            clickhouse_port=9000,
            clickhouse_database="nse_data_test",
            redis_host="localhost",
            redis_port=6379,
            redis_db=1,  # Use different DB for tests
        ),
    )


@pytest.fixture
def mock_clickhouse_connection():
    """Mock ClickHouse connection for testing."""
    mock_conn = Mock()
    mock_conn.execute.return_value = []
    mock_conn.query.return_value = []
    return mock_conn


@pytest.fixture
def mock_redis_connection():
    """Mock Redis connection for testing."""
    mock_redis = Mock()
    mock_redis.get.return_value = None  
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    return mock_redis


@pytest.fixture
def sample_equity_data():
    """Provide sample equity data for testing."""
    return {
        "symbol": "RELIANCE",
        "series": "EQ",
        "open": 2500.0,
        "high": 2550.0,
        "low": 2480.0,
        "close": 2520.0,
        "last": 2520.0,
        "prevClose": 2510.0,
        "tottrdqty": 1000000,
        "tottrdval": 2520000000.0,
        "timestamp": "2023-09-27T14:30:00+05:30",
        "totaltrades": 45000,
    }


@pytest.fixture
def sample_derivatives_data():
    """Provide sample derivatives data for testing."""
    return {
        "symbol": "RELIANCE",
        "expiryDate": "2023-10-26",
        "instrumentType": "FUTIDX",
        "strikePrice": 0.0,
        "optionType": "",
        "open": 2505.0,
        "high": 2555.0,
        "low": 2485.0,
        "close": 2525.0,
        "last": 2525.0,
        "prevClose": 2515.0,
        "volume": 500000,
        "value": 1262500000.0,
        "openInterest": 2000000,
        "changeInOI": 50000,
        "timestamp": "2023-09-27T14:30:00+05:30",
    }


@pytest.fixture
def temp_log_file(tmp_path):
    """Create temporary log file for testing."""
    log_file = tmp_path / "test.log"
    return str(log_file)


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("CLICKHOUSE_DATABASE", "nse_data_test")
    monkeypatch.setenv("REDIS_DB", "1")