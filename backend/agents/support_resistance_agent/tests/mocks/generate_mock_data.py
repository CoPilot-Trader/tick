"""
Script to generate realistic mock OHLCV data for testing.

This generates 2+ years of daily data for 5 tickers with:
- Realistic price movements
- Clear support/resistance levels
- Different patterns (trending, volatile, ranging)
- Volume data

Run this script to generate ohlcv_mock_data.json
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Set seed for reproducibility
random.seed(42)


def generate_ohlcv_data(
    symbol: str,
    start_price: float,
    days: int = 730,
    volatility: float = 0.02,
    trend: float = 0.0001,
    support_levels: list = None,
    resistance_levels: list = None
):
    """
    Generate realistic OHLCV data with support/resistance levels.
    
    Args:
        symbol: Stock symbol
        start_price: Starting price
        days: Number of days of data
        volatility: Daily volatility (0.02 = 2%)
        trend: Daily trend (0.0001 = slight upward trend)
        support_levels: List of support prices (price bounces up from these)
        resistance_levels: List of resistance prices (price bounces down from these)
    
    Returns:
        List of OHLCV data points
    """
    data = []
    current_price = start_price
    support_levels = support_levels or []
    resistance_levels = resistance_levels or []
    
    start_date = datetime(2022, 1, 1)
    
    for day in range(days):
        date = start_date + timedelta(days=day)
        
        # Check if near support/resistance
        near_support = False
        near_resistance = False
        
        for support in support_levels:
            if abs(current_price - support) / support < 0.02:  # Within 2%
                near_support = True
                # Bounce up from support
                current_price = support * (1 + random.uniform(0.01, 0.03))
                break
        
        for resistance in resistance_levels:
            if abs(current_price - resistance) / resistance < 0.02:  # Within 2%
                near_resistance = True
                # Bounce down from resistance
                current_price = resistance * (1 - random.uniform(0.01, 0.03))
                break
        
        # Generate price movement
        if not near_support and not near_resistance:
            # Normal random walk with trend
            change = random.gauss(trend, volatility)
            current_price *= (1 + change)
        
        # Generate OHLC from current price
        daily_volatility = random.uniform(0.005, 0.015)  # 0.5% to 1.5%
        
        open_price = current_price
        high_price = open_price * (1 + random.uniform(0, daily_volatility))
        low_price = open_price * (1 - random.uniform(0, daily_volatility))
        close_price = open_price * (1 + random.gauss(0, daily_volatility * 0.5))
        
        # Ensure high >= low and high/low are reasonable
        if high_price < low_price:
            high_price, low_price = low_price, high_price
        
        # Generate volume (higher on volatile days)
        base_volume = 1000000
        volume_multiplier = 1 + abs(close_price - open_price) / open_price * 10
        volume = int(base_volume * volume_multiplier * random.uniform(0.7, 1.3))
        
        data.append({
            "timestamp": date.isoformat() + "Z",
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        })
        
        # Update current price for next day
        current_price = close_price
    
    return data


def generate_all_mock_data():
    """Generate mock data for all tickers."""
    
    # Define ticker configurations
    tickers = {
        "AAPL": {
            "start_price": 150.0,
            "volatility": 0.02,
            "trend": 0.0001,
            "support_levels": [145.0, 140.0, 135.0],
            "resistance_levels": [155.0, 160.0, 165.0]
        },
        "TSLA": {
            "start_price": 250.0,
            "volatility": 0.035,  # More volatile
            "trend": 0.0002,
            "support_levels": [240.0, 230.0, 220.0],
            "resistance_levels": [260.0, 270.0, 280.0]
        },
        "MSFT": {
            "start_price": 380.0,
            "volatility": 0.018,
            "trend": 0.00015,
            "support_levels": [370.0, 360.0, 350.0],
            "resistance_levels": [390.0, 400.0, 410.0]
        },
        "GOOGL": {
            "start_price": 145.0,
            "volatility": 0.02,
            "trend": 0.0,  # Ranging market
            "support_levels": [140.0, 135.0, 130.0],
            "resistance_levels": [150.0, 155.0, 160.0]
        },
        "SPY": {
            "start_price": 450.0,
            "volatility": 0.015,
            "trend": 0.0001,
            "support_levels": [440.0, 430.0, 420.0],
            "resistance_levels": [460.0, 470.0, 480.0]
        }
    }
    
    mock_data = {}
    
    for symbol, config in tickers.items():
        print(f"Generating data for {symbol}...")
        data = generate_ohlcv_data(
            symbol=symbol,
            start_price=config["start_price"],
            days=730,  # 2 years
            volatility=config["volatility"],
            trend=config["trend"],
            support_levels=config["support_levels"],
            resistance_levels=config["resistance_levels"]
        )
        
        mock_data[symbol] = {
            "symbol": symbol,
            "sector": "Technology" if symbol != "SPY" else "Market Index",
            "data": data
        }
        
        print(f"  Generated {len(data)} days of data for {symbol}")
    
    return mock_data


if __name__ == "__main__":
    print("Generating mock OHLCV data...")
    mock_data = generate_all_mock_data()
    
    # Save to JSON file
    output_path = Path(__file__).parent / "ohlcv_mock_data.json"
    with open(output_path, 'w') as f:
        json.dump(mock_data, f, indent=2)
    
    print(f"\nMock data saved to: {output_path}")
    print(f"Total tickers: {len(mock_data)}")
    for symbol, data in mock_data.items():
        print(f"  {symbol}: {len(data['data'])} days")
