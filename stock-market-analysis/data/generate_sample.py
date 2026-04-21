"""
Generate Sample Data for GitHub Repository

Creates a sample CSV with 100 rows from the full dataset
to keep the repository size manageable.

Usage:
    python generate_sample.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))
from config import NIFTY_50_SYMBOLS, SECTOR_MAP


def generate_sample_data(n_rows: int = 100) -> pd.DataFrame:
    """
    Generate realistic sample stock data for GitHub.
    
    Args:
        n_rows: Number of rows to generate (default: 100)
        
    Returns:
        pd.DataFrame: Sample stock data
    """
    np.random.seed(42)
    
    # Select 5 stocks for sample
    sample_stocks = ['INFY', 'TCS', 'HDFCBANK', 'RELIANCE', 'TATAMOTORS']
    
    # Generate dates (20 trading days)
    start_date = datetime(2025, 1, 1)
    dates = []
    current_date = start_date
    while len(dates) < 20:
        if current_date.weekday() < 5:  # Weekdays only
            dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Generate data for each stock
    rows = []
    for symbol in sample_stocks:
        sector = SECTOR_MAP[symbol]
        
        # Base prices for different stocks
        base_prices = {
            'INFY': 1500,
            'TCS': 3500,
            'HDFCBANK': 1600,
            'RELIANCE': 2400,
            'TATAMOTORS': 750
        }
        
        base_price = base_prices[symbol]
        
        for date in dates:
            # Generate OHLCV data
            close = base_price + np.random.normal(0, base_price * 0.02)
            open_price = close + np.random.normal(0, base_price * 0.01)
            high = max(open_price, close) + abs(np.random.normal(0, base_price * 0.01))
            low = min(open_price, close) - abs(np.random.normal(0, base_price * 0.01))
            volume = int(np.random.uniform(1000000, 10000000))
            
            # Technical indicators
            rsi = np.random.uniform(25, 75)
            macd = np.random.normal(0, base_price * 0.005)
            macd_signal = macd + np.random.normal(0, base_price * 0.002)
            macd_hist = macd - macd_signal
            
            sma_20 = close + np.random.normal(0, base_price * 0.02)
            sma_50 = close + np.random.normal(0, base_price * 0.03)
            sma_200 = close + np.random.normal(0, base_price * 0.05)
            
            bb_upper = sma_20 + base_price * 0.04
            bb_lower = sma_20 - base_price * 0.04
            bb_mid = sma_20
            
            vol_zscore = np.random.normal(0, 1)
            daily_return = np.random.normal(0, 0.02)
            volatility_20d = abs(np.random.uniform(0.15, 0.45))
            
            # Generate signal
            if rsi < 40 or (macd > macd_signal and macd_hist > 0):
                signal = 'BUY'
            elif rsi > 70 or (macd < macd_signal and macd_hist < 0):
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            rows.append({
                'date': date,
                'symbol': symbol,
                'sector': sector,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close, 2),
                'volume': volume,
                'rsi_14': round(rsi, 2),
                'macd': round(macd, 4),
                'macd_signal': round(macd_signal, 4),
                'macd_hist': round(macd_hist, 4),
                'sma_20': round(sma_20, 2),
                'sma_50': round(sma_50, 2),
                'sma_200': round(sma_200, 2),
                'bb_upper': round(bb_upper, 2),
                'bb_lower': round(bb_lower, 2),
                'bb_mid': round(bb_mid, 2),
                'vol_zscore': round(vol_zscore, 4),
                'daily_return': round(daily_return, 6),
                'volatility_20d': round(volatility_20d, 6),
                'signal': signal
            })
    
    df = pd.DataFrame(rows)
    
    # Shuffle and select n_rows
    df = df.sample(n=min(n_rows, len(df)), random_state=42).reset_index(drop=True)
    
    return df


if __name__ == '__main__':
    print("Generating sample data...")
    
    # Generate sample
    sample_df = generate_sample_data(100)
    
    # Save to CSV
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'nse_bse_features.csv')
    sample_df.to_csv(output_path, index=False)
    
    print(f"Sample data saved to: {output_path}")
    print(f"Rows: {len(sample_df)}")
    print(f"Columns: {len(sample_df.columns)}")
    print(f"Stocks: {sample_df['symbol'].unique()}")
    print(f"Sectors: {sample_df['sector'].unique()}")
    print(f"Signal distribution:")
    print(sample_df['signal'].value_counts())
