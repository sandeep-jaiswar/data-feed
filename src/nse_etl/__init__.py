"""
NSE Data ETL - High-performance financial data processing system.

This package provides comprehensive ETL capabilities for NSE (National Stock Exchange)
financial data with investment banking standards for performance and reliability.
"""

__version__ = "0.1.0"
__author__ = "NSE Data ETL Team"
__email__ = "team@nse-data-etl.com"

# Package-level imports for convenience
from .config import Settings, get_settings
from .logging import setup_logging

__all__ = [
    "__version__",
    "Settings",
    "get_settings", 
    "setup_logging",
]