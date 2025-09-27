"""
Structured logging configuration using Loguru.

Provides high-performance, structured logging with JSON output for production
and human-readable output for development. Includes performance monitoring
and request tracing capabilities.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

from loguru import logger

from .config import Settings, Environment


def setup_logging(settings: Optional[Settings] = None) -> None:
    """
    Configure structured logging with Loguru.
    
    Sets up logging based on environment with appropriate formatters,
    handlers, and performance optimizations for financial data processing.
    
    Args:
        settings: Application settings (optional, will load if not provided)
    """
    if settings is None:
        from .config import get_settings
        settings = get_settings()
    
    # Remove default logger
    logger.remove()
    
    # Configure format based on environment
    if settings.log_format.lower() == "json":
        log_format = _get_json_format()
    else:
        log_format = _get_text_format()
    
    # Console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.log_level,
        colorize=settings.environment == Environment.DEVELOPMENT,
        backtrace=settings.debug,
        diagnose=settings.debug,
        enqueue=True,  # Thread-safe logging
    )
    
    # File handler (if specified)
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            str(log_path),
            format=_get_json_format(),  # Always JSON for file logs
            level=settings.log_level,
            rotation="100 MB",
            retention="30 days",
            compression="gz",
            backtrace=settings.debug,
            diagnose=settings.debug,
            enqueue=True,
        )
    
    # Add custom context for financial data processing
    logger.configure(
        extra={
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
        }
    )
    
    # Log startup information
    logger.info(
        "Logging configured",
        level=settings.log_level,
        format=settings.log_format,
        environment=settings.environment.value,
        debug=settings.debug,
    )


def _get_json_format() -> str:
    """Get JSON log format for structured logging."""
    return (
        "{"
        '"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
        '"level": "{level}", '
        '"service": "{extra[service]}", '
        '"version": "{extra[version]}", '
        '"environment": "{extra[environment]}", '
        '"module": "{module}", '
        '"function": "{function}", '
        '"line": {line}, '
        '"message": "{message}", '
        '"extra": {extra}'
        "}"
    )


def _get_text_format() -> str:
    """Get human-readable log format for development."""
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[service]}</cyan> | "
        "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )


def get_logger(name: str) -> "logger":
    """
    Get a named logger instance with context.
    
    Args:
        name: Logger name (typically module name)
        
    Returns:
        Configured logger instance with context
    """
    return logger.bind(component=name)


class RequestLogger:
    """Request logging middleware for performance monitoring."""
    
    def __init__(self, logger_name: str = "request"):
        self.logger = get_logger(logger_name)
    
    async def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        request_id: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log HTTP request with performance metrics.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            response_time: Response time in milliseconds
            request_id: Unique request identifier
            extra: Additional context data
        """
        log_data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time_ms": round(response_time, 2),
            "request_type": "http",
        }
        
        if extra:
            log_data.update(extra)
        
        # Log level based on status code and response time
        if status_code >= 500:
            level = "error"
        elif status_code >= 400:
            level = "warning"
        elif response_time > 1000:  # Slow request (>1s)
            level = "warning"
        else:
            level = "info"
        
        getattr(self.logger, level)(
            f"{method} {path} - {status_code} ({response_time:.2f}ms)",
            **log_data
        )


class DataProcessingLogger:
    """Specialized logger for data processing operations."""
    
    def __init__(self, logger_name: str = "data_processing"):
        self.logger = get_logger(logger_name)
    
    def log_batch_processing(
        self,
        operation: str,
        records_processed: int,
        processing_time: float,
        success_rate: float,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log batch processing metrics.
        
        Args:
            operation: Processing operation name
            records_processed: Number of records processed
            processing_time: Processing time in seconds
            success_rate: Success rate (0.0 to 1.0)
            extra: Additional context data
        """
        log_data = {
            "operation": operation,
            "records_processed": records_processed,
            "processing_time_s": round(processing_time, 3),
            "success_rate": round(success_rate, 4),
            "records_per_second": round(records_processed / processing_time, 2) if processing_time > 0 else 0,
            "operation_type": "batch_processing",
        }
        
        if extra:
            log_data.update(extra)
        
        # Log level based on success rate and performance
        if success_rate < 0.95:  # Less than 95% success
            level = "error"
        elif success_rate < 0.99:  # Less than 99% success
            level = "warning"
        elif records_processed / processing_time < 100:  # Less than 100 records/sec
            level = "warning"
        else:
            level = "info"
        
        getattr(self.logger, level)(
            f"Batch {operation}: {records_processed} records processed "
            f"in {processing_time:.3f}s ({success_rate:.2%} success rate)",
            **log_data
        )