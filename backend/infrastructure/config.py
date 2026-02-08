"""
Configuration management for TICK backend.
Loads settings from environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "TICK"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database (TimescaleDB)
    database_url: str = Field(
        default="postgresql://tick_user:tick_password@localhost:5432/tick_db",
        description="PostgreSQL/TimescaleDB connection URL"
    )
    db_pool_size: int = 5
    db_max_overflow: int = 10
    
    # Redis Cache
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    cache_ttl_seconds: int = 300  # 5 minutes default TTL
    
    # Data Sources
    alpha_vantage_api_key: Optional[str] = Field(
        default=None,
        description="Alpha Vantage API key for market data"
    )
    
    # Data Agent Settings
    default_tickers: list = ["AAPL", "TSLA", "MSFT", "GOOGL", "SPY"]
    historical_years: int = 2
    streaming_interval_seconds: int = 300  # 5 minutes
    
    # Feature Agent Settings
    feature_cache_ttl: int = 60  # 1 minute for live features
    
    # Storage
    storage_path: str = "storage/historical"
    
    # News Agent (Developer 1's work - for compatibility)
    finnhub_api_key: Optional[str] = None
    newsapi_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
