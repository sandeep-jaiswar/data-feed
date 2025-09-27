"""
Data models for NSE ETL pipeline.

Defines Pydantic models for financial data with proper validation and type safety.
Following investment banking standards for financial data precision and validation.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, validator, root_validator
import pytz


class TradeType(str, Enum):
    """Types of market data events."""
    TRADE = "TRADE"
    BID = "BID"
    ASK = "ASK"
    LAST = "LAST"


class Timeframe(str, Enum):
    """Supported timeframes for OHLCV data."""
    ONE_MINUTE = "1m"
    FIVE_MINUTE = "5m"
    FIFTEEN_MINUTE = "15m"
    THIRTY_MINUTE = "30m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"


class EventType(str, Enum):
    """Types of market events."""
    DIVIDEND = "DIVIDEND"
    BONUS = "BONUS"
    SPLIT = "SPLIT"
    RIGHTS = "RIGHTS"
    MERGER = "MERGER"
    DELISTING = "DELISTING"
    NEWS = "NEWS"
    RESULT = "RESULT"
    AGM = "AGM"


class MoverCategory(str, Enum):
    """Categories for market movers."""
    GAINERS = "GAINERS"
    LOSERS = "LOSERS"
    ACTIVE = "ACTIVE"
    HIGH_VALUE = "HIGH_VALUE"
    HIGH_VOLUME = "HIGH_VOLUME"


class RawTick(BaseModel):
    """
    Raw tick data model with financial precision and validation.
    
    Represents individual trade/quote events from NSE with full precision
    for financial calculations and compliance requirements.
    """
    symbol: str = Field(..., description="NSE trading symbol", max_length=20)
    timestamp: datetime = Field(..., description="Trade timestamp in UTC")
    price: Decimal = Field(..., description="Trade price with full precision", decimal_places=2)
    volume: int = Field(..., description="Trade volume/quantity", ge=0)
    bid_price: Optional[Decimal] = Field(None, description="Best bid price", decimal_places=2)
    ask_price: Optional[Decimal] = Field(None, description="Best ask price", decimal_places=2)
    bid_size: Optional[int] = Field(None, description="Best bid quantity", ge=0)
    ask_size: Optional[int] = Field(None, description="Best ask quantity", ge=0)
    exchange: str = Field(default="NSE", description="Exchange identifier")
    source: str = Field(..., description="Data source identifier")
    trade_id: Optional[str] = Field(None, description="Unique trade identifier")
    trade_type: TradeType = Field(default=TradeType.TRADE, description="Type of market data event")
    inserted_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="ETL insertion timestamp")

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate NSE symbol format."""
        if not v or len(v) < 1:
            raise ValueError("Symbol cannot be empty")
        return v.upper().strip()

    @validator('price', 'bid_price', 'ask_price')
    def validate_price(cls, v):
        """Validate price values are positive."""
        if v is not None and v <= 0:
            raise ValueError("Price must be positive")
        return v

    @validator('timestamp', 'inserted_at')
    def validate_timezone(cls, v):
        """Ensure timestamps are in UTC."""
        if v is not None and v.tzinfo is None:
            # Assume UTC if no timezone info
            return v.replace(tzinfo=pytz.UTC)
        return v

    @root_validator
    def validate_bid_ask_spread(cls, values):
        """Validate bid-ask spread is reasonable."""
        bid_price = values.get('bid_price')
        ask_price = values.get('ask_price')
        
        if bid_price is not None and ask_price is not None:
            if bid_price >= ask_price:
                # Allow equal bid/ask for certain market conditions
                pass
            elif (ask_price - bid_price) / bid_price > 0.1:  # 10% spread limit
                raise ValueError("Bid-ask spread too wide (>10%)")
        
        return values

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        str_strip_whitespace = True


class OHLCVBar(BaseModel):
    """
    OHLCV bar data model for aggregated price data.
    
    Represents time-based aggregated data with proper financial calculations
    and validation for technical analysis and reporting.
    """
    symbol: str = Field(..., description="NSE trading symbol", max_length=20)
    timeframe: Timeframe = Field(..., description="Bar timeframe")
    timestamp: datetime = Field(..., description="Bar start timestamp")
    open: Decimal = Field(..., description="Opening price", decimal_places=2)
    high: Decimal = Field(..., description="Highest price", decimal_places=2)
    low: Decimal = Field(..., description="Lowest price", decimal_places=2)
    close: Decimal = Field(..., description="Closing price", decimal_places=2)
    volume: int = Field(..., description="Total volume", ge=0)
    trade_count: int = Field(..., description="Number of trades", ge=0)
    vwap: Decimal = Field(..., description="Volume Weighted Average Price", decimal_places=2)
    turnover: Decimal = Field(..., description="Total value traded", decimal_places=2)
    first_trade_time: datetime = Field(..., description="First trade timestamp")
    last_trade_time: datetime = Field(..., description="Last trade timestamp")
    inserted_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate NSE symbol format."""
        return v.upper().strip()

    @root_validator
    def validate_ohlcv(cls, values):
        """Validate OHLCV relationships."""
        open_price = values.get('open')
        high_price = values.get('high') 
        low_price = values.get('low')
        close_price = values.get('close')
        
        if all(p is not None for p in [open_price, high_price, low_price, close_price]):
            # High should be >= all other prices
            if not (high_price >= open_price and high_price >= close_price and high_price >= low_price):
                raise ValueError("High price must be >= open, close, and low prices")
            
            # Low should be <= all other prices
            if not (low_price <= open_price and low_price <= close_price and low_price <= high_price):
                raise ValueError("Low price must be <= open, close, and high prices")
        
        return values

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class SymbolMaster(BaseModel):
    """
    Symbol master data model for NSE trading symbols.
    
    Contains reference information for symbols including corporate details,
    trading parameters, and market classifications.
    """
    symbol: str = Field(..., description="NSE trading symbol", max_length=20)
    company_name: str = Field(..., description="Full company name", max_length=255)
    isin: str = Field(..., description="ISIN code", max_length=12)
    sector: str = Field(..., description="Business sector", max_length=100)
    industry: str = Field(..., description="Industry classification", max_length=100)
    market_cap: Optional[int] = Field(None, description="Market cap in INR", ge=0)
    face_value: Optional[Decimal] = Field(None, description="Face value", decimal_places=2)
    listing_date: Optional[date] = Field(None, description="Listing date")
    upper_circuit: Optional[Decimal] = Field(None, description="Upper circuit limit", decimal_places=2)
    lower_circuit: Optional[Decimal] = Field(None, description="Lower circuit limit", decimal_places=2)
    lot_size: int = Field(default=1, description="Trading lot size", ge=1)
    tick_size: Decimal = Field(default=Decimal('0.01'), description="Minimum price movement", decimal_places=2)
    is_active: bool = Field(default=True, description="Whether actively traded")
    exchange: str = Field(default="NSE", description="Exchange identifier")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate NSE symbol format."""
        return v.upper().strip()

    @validator('isin')
    def validate_isin(cls, v):
        """Basic ISIN format validation."""
        if v and len(v) not in [0, 12]:
            raise ValueError("ISIN must be 12 characters or empty")
        return v.upper() if v else v

    @root_validator
    def validate_circuits(cls, values):
        """Validate circuit limits."""
        upper = values.get('upper_circuit')
        lower = values.get('lower_circuit')
        
        if upper is not None and lower is not None:
            if upper <= lower:
                raise ValueError("Upper circuit must be greater than lower circuit")
        
        return values

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class MarketEvent(BaseModel):
    """
    Market event data model for corporate actions and news.
    
    Tracks corporate actions, results, and other market-moving events
    that affect symbol prices and trading behavior.
    """
    id: int = Field(..., description="Unique event identifier")
    symbol: str = Field(..., description="Affected symbol", max_length=20)
    event_type: EventType = Field(..., description="Type of event")
    event_date: date = Field(..., description="Event occurrence date")
    ex_date: Optional[date] = Field(None, description="Ex-date")
    record_date: Optional[date] = Field(None, description="Record date")
    event_description: str = Field(..., description="Event description", max_length=1000)
    impact_factor: Optional[Decimal] = Field(None, description="Impact factor", decimal_places=4)
    announcement_date: date = Field(..., description="Announcement date")
    source: str = Field(..., description="Information source", max_length=50)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate NSE symbol format."""
        return v.upper().strip()

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class DataQualityMetrics(BaseModel):
    """
    Data quality metrics model for monitoring data health.
    
    Tracks completeness, accuracy, and other quality indicators
    for data monitoring and alerting systems.
    """
    date: date = Field(..., description="Metrics date")
    symbol: str = Field(..., description="Symbol", max_length=20)
    total_ticks: int = Field(..., description="Total ticks", ge=0)
    valid_ticks: int = Field(..., description="Valid ticks", ge=0)
    invalid_ticks: int = Field(..., description="Invalid ticks", ge=0)
    duplicate_ticks: int = Field(..., description="Duplicate ticks", ge=0)
    missing_minutes: int = Field(..., description="Missing minutes", ge=0)
    price_anomalies: int = Field(..., description="Price anomalies", ge=0)
    volume_anomalies: int = Field(..., description="Volume anomalies", ge=0)
    data_completeness_pct: Decimal = Field(..., description="Completeness %", decimal_places=2)
    data_accuracy_pct: Decimal = Field(..., description="Accuracy %", decimal_places=2)
    first_tick_time: datetime = Field(..., description="First tick time")
    last_tick_time: datetime = Field(..., description="Last tick time")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate NSE symbol format."""
        return v.upper().strip()

    @validator('data_completeness_pct', 'data_accuracy_pct')
    def validate_percentage(cls, v):
        """Validate percentage values."""
        if v < 0 or v > 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class MarketMover(BaseModel):
    """
    Market mover data model for top gainers/losers tracking.
    
    Pre-computed rankings for fast API responses and market analysis.
    """
    date: date = Field(..., description="Trading date")
    timeframe: Timeframe = Field(..., description="Analysis timeframe") 
    category: MoverCategory = Field(..., description="Mover category")
    symbol: str = Field(..., description="Symbol", max_length=20)
    price: Decimal = Field(..., description="Current price", decimal_places=2)
    change_pct: Decimal = Field(..., description="Percentage change", decimal_places=2)
    volume: int = Field(..., description="Volume", ge=0)
    turnover: Decimal = Field(..., description="Turnover", decimal_places=2)
    rank: int = Field(..., description="Rank in category", ge=1, le=100)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate NSE symbol format."""
        return v.upper().strip()

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class SymbolStatistics(BaseModel):
    """
    Symbol statistics model for technical indicators and metrics.
    
    Pre-calculated technical indicators and statistical measures
    for efficient market analysis and screening.
    """
    symbol: str = Field(..., description="Symbol", max_length=20)
    date: date = Field(..., description="Calculation date")
    avg_price: Decimal = Field(..., description="Average price", decimal_places=2)
    volatility: Decimal = Field(..., description="Price volatility", decimal_places=4)
    beta: Decimal = Field(..., description="Beta coefficient", decimal_places=4)
    avg_volume: int = Field(..., description="Average volume", ge=0)
    avg_turnover: Decimal = Field(..., description="Average turnover", decimal_places=2)
    trading_sessions: int = Field(..., description="Trading sessions", ge=0)
    price_range_high: Decimal = Field(..., description="High price", decimal_places=2)
    price_range_low: Decimal = Field(..., description="Low price", decimal_places=2)
    support_level: Decimal = Field(..., description="Support level", decimal_places=2)
    resistance_level: Decimal = Field(..., description="Resistance level", decimal_places=2)
    rsi: Decimal = Field(..., description="RSI", decimal_places=2)
    sma_20: Decimal = Field(..., description="20-period SMA", decimal_places=2)
    ema_20: Decimal = Field(..., description="20-period EMA", decimal_places=2)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate NSE symbol format."""
        return v.upper().strip()

    @validator('rsi')
    def validate_rsi(cls, v):
        """Validate RSI range."""
        if v < 0 or v > 100:
            raise ValueError("RSI must be between 0 and 100")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


def normalize_nse_symbol(symbol: str) -> str:
    """
    Normalize NSE symbol format.
    
    Args:
        symbol: Raw symbol string
        
    Returns:
        Normalized symbol string
    """
    if not symbol:
        return symbol
    
    # Remove -EQ suffix and normalize
    normalized = symbol.upper().strip().replace('-EQ', '')
    return normalized


def validate_market_hours(timestamp: datetime) -> bool:
    """
    Check if timestamp falls within NSE market hours.
    
    Args:
        timestamp: Timestamp to validate
        
    Returns:
        True if within market hours
    """
    if not timestamp:
        return False
    
    # Convert to IST
    ist = pytz.timezone('Asia/Kolkata')
    if timestamp.tzinfo is None:
        timestamp = pytz.UTC.localize(timestamp)
    
    ist_time = timestamp.astimezone(ist)
    
    # NSE market hours: 9:15 AM - 3:30 PM IST
    market_open = ist_time.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = ist_time.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_open <= ist_time <= market_close


def calculate_percentage_change(old_price: Decimal, new_price: Decimal) -> Decimal:
    """
    Calculate percentage change with proper precision.
    
    Args:
        old_price: Previous price
        new_price: Current price
        
    Returns:
        Percentage change
    """
    if old_price == 0:
        return Decimal('0')
    
    return ((new_price - old_price) / old_price) * Decimal('100')