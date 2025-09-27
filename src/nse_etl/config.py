"""
Configuration management using Pydantic settings.

Provides environment-specific configuration with validation and type safety.
Supports dev, staging, and production environments with secure secrets handling.
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional, List

from pydantic import BaseSettings, Field, validator


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # ClickHouse settings
    clickhouse_host: str = Field(default="localhost", env="CLICKHOUSE_HOST")
    clickhouse_port: int = Field(default=9000, env="CLICKHOUSE_PORT")
    clickhouse_database: str = Field(default="nse_data", env="CLICKHOUSE_DATABASE")
    clickhouse_user: str = Field(default="default", env="CLICKHOUSE_USER")
    clickhouse_password: str = Field(default="", env="CLICKHOUSE_PASSWORD")
    
    # Redis settings
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")


class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings."""
    
    # Prometheus settings
    prometheus_host: str = Field(default="localhost", env="PROMETHEUS_HOST")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # Metrics settings
    metrics_port: int = Field(default=8000, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # Alerting
    alert_webhook_url: Optional[str] = Field(default=None, env="ALERT_WEBHOOK_URL")


class CollectorSettings(BaseSettings):
    """Data collector configuration."""
    
    # NSE API settings
    nse_base_url: str = Field(default="https://www.nseindia.com", env="NSE_BASE_URL")
    nse_api_timeout: int = Field(default=30, env="NSE_API_TIMEOUT")
    nse_rate_limit: int = Field(default=100, env="NSE_RATE_LIMIT")  # requests per minute
    
    # WebSocket settings
    websocket_url: Optional[str] = Field(default=None, env="WEBSOCKET_URL")
    websocket_reconnect_interval: int = Field(default=5, env="WEBSOCKET_RECONNECT_INTERVAL")
    
    # Data collection intervals (seconds)
    equity_data_interval: int = Field(default=1, env="EQUITY_DATA_INTERVAL")
    derivatives_data_interval: int = Field(default=1, env="DERIVATIVES_DATA_INTERVAL")
    indices_data_interval: int = Field(default=5, env="INDICES_DATA_INTERVAL")


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
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v
    
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