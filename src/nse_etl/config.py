"""
Configuration management using Pydantic settings.

Provides environment-specific configuration with validation and type safety.
Supports dev, staging, and production environments with secure secrets handling.
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional, List

from pydantic import Field
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # Database settings
    clickhouse_host: str = Field(default="localhost", description="ClickHouse host")
    clickhouse_port: int = Field(default=9000, description="ClickHouse port")
    clickhouse_database: str = Field(default="nse_data", description="ClickHouse database")
    clickhouse_user: str = Field(default="default", description="ClickHouse user")
    clickhouse_password: str = Field(default="", description="ClickHouse password")
    
    # Redis settings
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database")
    redis_password: Optional[str] = Field(default=None, description="Redis password")


class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings."""
    
    # Prometheus settings
    prometheus_host: str = Field(default="localhost", description="Prometheus host")
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    
    # Metrics settings
    metrics_port: int = Field(default=8000, description="Metrics port")
    health_check_interval: int = Field(default=30, description="Health check interval")
    
    # Alerting
    alert_webhook_url: Optional[str] = Field(default=None, description="Alert webhook URL")


class CollectorSettings(BaseSettings):
    """Data collector configuration."""
    
    # NSE API settings
    nse_base_url: str = Field(default="https://www.nseindia.com", description="NSE base URL")
    nse_api_timeout: int = Field(default=30, description="NSE API timeout")
    nse_rate_limit: int = Field(default=100, description="NSE rate limit")  # requests per minute
    
    # WebSocket settings
    websocket_url: Optional[str] = Field(default=None, description="WebSocket URL")
    websocket_reconnect_interval: int = Field(default=5, description="WebSocket reconnect interval")
    
    # Data collection intervals (seconds)
    equity_data_interval: int = Field(default=1, description="Equity data interval")
    derivatives_data_interval: int = Field(default=1, description="Derivatives data interval")
    indices_data_interval: int = Field(default=5, description="Indices data interval")


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application settings
    app_name: str = Field(default="NSE Data ETL", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8080, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    
    # Security settings
    secret_key: str = Field(env="SECRET_KEY")
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Performance settings
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    batch_size: int = Field(default=1000, env="BATCH_SIZE")
    queue_size: int = Field(default=10000, env="QUEUE_SIZE")
    
    # Nested settings
    database: DatabaseSettings = DatabaseSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    collector: CollectorSettings = CollectorSettings()
    
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        use_enum_values = True
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        use_enum_values = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses LRU cache to avoid reloading settings on every call.
    Cache is cleared when process restarts.
    
    Returns:
        Settings: Application configuration settings
    """
    return Settings()


def get_config_path(env: Environment) -> Path:
    """
    Get configuration file path for specific environment.
    
    Args:
        env: Target environment
        
    Returns:
        Path: Configuration file path
    """
    base_path = Path(__file__).parent.parent.parent / "configs"
    return base_path / env.value / "config.yaml"