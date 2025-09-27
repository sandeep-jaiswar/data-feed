"""
Unit tests for configuration management.

Tests the Pydantic settings validation and environment variable handling.
"""

import pytest
from unittest.mock import patch
import os

from nse_etl.config import Settings, Environment, get_settings


class TestSettings:
    """Test Settings class and validation."""
    
    def test_default_settings(self):
        """Test default settings initialization."""
        with patch.dict(os.environ, {"SECRET_KEY": "test-key"}, clear=True):
            settings = Settings()
            
            assert settings.app_name == "NSE Data ETL"
            assert settings.environment == Environment.DEVELOPMENT
            assert settings.debug is False
            assert settings.log_level == "INFO"
            assert settings.api_port == 8080

    def test_environment_variable_override(self):
        """Test environment variable override."""
        env_vars = {
            "SECRET_KEY": "test-key",
            "APP_NAME": "Test App",
            "ENVIRONMENT": "production",
            "DEBUG": "true",
            "LOG_LEVEL": "debug",
            "API_PORT": "9000",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            assert settings.app_name == "Test App"
            assert settings.environment == Environment.PRODUCTION
            assert settings.debug is True
            assert settings.log_level == "DEBUG"
            assert settings.api_port == 9000

    def test_nested_settings(self):
        """Test nested settings configuration."""
        env_vars = {
            "SECRET_KEY": "test-key",
            "CLICKHOUSE_HOST": "test-host",
            "CLICKHOUSE_PORT": "8123",
            "REDIS_HOST": "redis-host",
            "REDIS_PORT": "6380",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            assert settings.database.clickhouse_host == "test-host"
            assert settings.database.clickhouse_port == 8123
            assert settings.database.redis_host == "redis-host"
            assert settings.database.redis_port == 6380

    def test_log_level_validation(self):
        """Test log level validation."""
        with patch.dict(os.environ, {"SECRET_KEY": "test-key", "LOG_LEVEL": "invalid"}, clear=True):
            with pytest.raises(ValueError, match="Log level must be one of"):
                Settings()

    def test_environment_validation(self):
        """Test environment validation."""
        with patch.dict(os.environ, {"SECRET_KEY": "test-key", "ENVIRONMENT": "testing"}, clear=True):
            with pytest.raises(ValueError):
                Settings()

    def test_secret_key_required(self):
        """Test that secret key is required."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                Settings()


class TestGetSettings:
    """Test get_settings function and caching."""
    
    def test_get_settings_returns_settings(self):
        """Test that get_settings returns Settings instance."""
        with patch.dict(os.environ, {"SECRET_KEY": "test-key"}, clear=True):
            settings = get_settings()
            assert isinstance(settings, Settings)

    def test_get_settings_caching(self):
        """Test that get_settings uses LRU cache."""
        with patch.dict(os.environ, {"SECRET_KEY": "test-key"}, clear=True):
            settings1 = get_settings()
            settings2 = get_settings()
            
            # Should be the same instance due to caching
            assert settings1 is settings2

    def test_get_settings_cache_clear(self):
        """Test cache clearing functionality."""
        with patch.dict(os.environ, {"SECRET_KEY": "test-key"}, clear=True):
            # Clear cache and test
            get_settings.cache_clear()
            settings = get_settings()
            assert isinstance(settings, Settings)


class TestEnvironmentEnum:
    """Test Environment enum."""
    
    def test_environment_values(self):
        """Test environment enum values."""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"

    def test_environment_from_string(self):
        """Test creating environment from string."""
        assert Environment("development") == Environment.DEVELOPMENT
        assert Environment("staging") == Environment.STAGING
        assert Environment("production") == Environment.PRODUCTION