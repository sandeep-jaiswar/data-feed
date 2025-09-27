"""
Data Collectors Module.

Handles collection of financial data from various sources including:
- NSE real-time feeds
- Historical data APIs
- WebSocket streams
- FTP data sources
"""

from .base import BaseCollector
from .nse_collector import NSECollector
from .websocket_collector import WebSocketCollector

__all__ = [
    "BaseCollector",
    "NSECollector", 
    "WebSocketCollector",
]