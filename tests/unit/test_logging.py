"""
Unit tests for logging configuration.

Tests the Loguru-based structured logging setup and functionality.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from nse_etl.logging import setup_logging, get_logger, RequestLogger, DataProcessingLogger
from nse_etl.config import Settings, Environment


class TestSetupLogging:
    """Test logging setup functionality."""
    
    def test_setup_logging_development(self, test_settings, temp_log_file):
        """Test logging setup for development environment."""
        test_settings.environment = Environment.DEVELOPMENT
        test_settings.log_level = "DEBUG"
        test_settings.log_format = "text"
        test_settings.debug = True
        
        # Should not raise any exceptions
        setup_logging(test_settings)
        
        # Test that logger works
        logger = get_logger("test")
        logger.info("Test message")  # Should not raise

    def test_setup_logging_production(self, test_settings, temp_log_file):
        """Test logging setup for production environment."""
        test_settings.environment = Environment.PRODUCTION
        test_settings.log_level = "INFO"
        test_settings.log_format = "json"
        test_settings.log_file = temp_log_file
        test_settings.debug = False
        
        # Should not raise any exceptions
        setup_logging(test_settings)
        
        # Test that logger works
        logger = get_logger("test")
        logger.info("Test message")  # Should not raise
        
        # Check that log file was created
        assert Path(temp_log_file).exists()

    def test_setup_logging_with_file(self, test_settings, temp_log_file):
        """Test logging setup with file output."""
        test_settings.log_file = temp_log_file
        
        setup_logging(test_settings)
        
        logger = get_logger("test")
        logger.info("Test file message")
        
        # File should exist and contain content
        log_path = Path(temp_log_file)
        assert log_path.exists()
        assert log_path.stat().st_size > 0

    def test_setup_logging_creates_log_directory(self, test_settings, tmp_path):
        """Test that logging setup creates log directory if it doesn't exist."""
        log_dir = tmp_path / "logs" / "nested"
        log_file = log_dir / "test.log"
        test_settings.log_file = str(log_file)
        
        setup_logging(test_settings)
        
        assert log_dir.exists()


class TestGetLogger:
    """Test get_logger function."""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test")
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")

    def test_get_logger_with_context(self):
        """Test that get_logger adds context."""
        logger = get_logger("test_module")
        # Should not raise - testing that context is properly bound
        logger.info("Test message with context")


class TestRequestLogger:
    """Test RequestLogger class."""
    
    def test_request_logger_initialization(self):
        """Test RequestLogger initialization."""
        request_logger = RequestLogger("test_requests")
        assert request_logger.logger is not None

    @pytest.mark.asyncio
    async def test_log_request_success(self):
        """Test logging successful request."""
        request_logger = RequestLogger("test_requests")
        
        await request_logger.log_request(
            method="GET",
            path="/api/data",
            status_code=200,
            response_time=150.5,
            request_id="req-123",
            extra={"user_id": "user-456"}
        )
        # Should complete without error

    @pytest.mark.asyncio
    async def test_log_request_error(self):
        """Test logging error request."""
        request_logger = RequestLogger("test_requests")
        
        await request_logger.log_request(
            method="POST",
            path="/api/process",
            status_code=500,
            response_time=5000.0,
            request_id="req-456"
        )
        # Should complete without error

    @pytest.mark.asyncio
    async def test_log_request_slow(self):
        """Test logging slow request."""
        request_logger = RequestLogger("test_requests")
        
        await request_logger.log_request(
            method="GET",
            path="/api/slow",
            status_code=200,
            response_time=1500.0,  # > 1000ms = slow
            request_id="req-789"
        )
        # Should complete without error


class TestDataProcessingLogger:
    """Test DataProcessingLogger class."""
    
    def test_data_processing_logger_initialization(self):
        """Test DataProcessingLogger initialization."""
        data_logger = DataProcessingLogger("test_processing")
        assert data_logger.logger is not None

    def test_log_batch_processing_success(self):
        """Test logging successful batch processing."""
        data_logger = DataProcessingLogger("test_processing")
        
        data_logger.log_batch_processing(
            operation="equity_data_ingestion",
            records_processed=1000,
            processing_time=2.5,
            success_rate=1.0,
            extra={"batch_id": "batch-123"}
        )
        # Should complete without error

    def test_log_batch_processing_partial_failure(self):
        """Test logging batch processing with partial failures."""
        data_logger = DataProcessingLogger("test_processing")
        
        data_logger.log_batch_processing(
            operation="derivatives_processing",
            records_processed=500,
            processing_time=1.0,
            success_rate=0.96,  # < 99% success
            extra={"errors": 20}
        )
        # Should complete without error

    def test_log_batch_processing_major_failure(self):
        """Test logging batch processing with major failures."""
        data_logger = DataProcessingLogger("test_processing")
        
        data_logger.log_batch_processing(
            operation="data_validation",
            records_processed=100,
            processing_time=0.5,
            success_rate=0.90,  # < 95% success
        )
        # Should complete without error

    def test_log_batch_processing_slow_performance(self):
        """Test logging slow batch processing."""
        data_logger = DataProcessingLogger("test_processing")
        
        data_logger.log_batch_processing(
            operation="technical_indicators",
            records_processed=50,  # < 100 records/sec
            processing_time=1.0,
            success_rate=1.0,
        )
        # Should complete without error