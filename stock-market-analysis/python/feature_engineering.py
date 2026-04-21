"""
Feature Engineering Module for Stock Market Technical Indicators.

Provides pure functions for computing technical indicators including:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Simple Moving Averages (SMA)
- Bollinger Bands
- Volume Z-Score
- Volatility
- Trading Signals (BUY/SELL/HOLD)

All functions include type hints, docstrings, error handling, and logging.
"""

import logging
import numpy as np
import pandas as pd
from typing import Tuple

logger = logging.getLogger("stock_analysis")


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    RSI measures the speed and magnitude of recent price changes to evaluate
    overbought or oversold conditions. Values range from 0 to 100.
    
    Args:
        close: Series of closing prices
        period: Lookback period for RSI calculation (default: 14)
        
    Returns:
        pd.Series: RSI values
        
    Example:
        >>> close = pd.Series([100, 102, 101, 103, 105, 104, 106])
        >>> rsi = calculate_rsi(close, period=3)
    """
    try:
        delta = close.diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        logger.debug(f"RSI calculated with period={period}")
        return rsi
        
    except Exception as e:
        logger.error(f"Error calculating RSI: {str(e)}")
        return pd.Series(np.nan, index=close.index)


def calculate_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Moving Average Convergence Divergence (MACD).
    
    MACD shows the relationship between two moving averages of closing prices.
    Returns three series: MACD line, Signal line, and Histogram.
    
    Args:
        close: Series of closing prices
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line EMA period (default: 9)
        
    Returns:
        Tuple of (macd_line, signal_line, macd_histogram)
        
    Example:
        >>> macd_line, signal_line, histogram = calculate_macd(close)
    """
    try:
        # Calculate EMAs
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        # Histogram
        macd_histogram = macd_line - signal_line
        
        logger.debug(f"MACD calculated with fast={fast}, slow={slow}, signal={signal}")
        return macd_line, signal_line, macd_histogram
        
    except Exception as e:
        logger.error(f"Error calculating MACD: {str(e)}")
        return (
            pd.Series(np.nan, index=close.index),
            pd.Series(np.nan, index=close.index),
            pd.Series(np.nan, index=close.index)
        )


def calculate_sma(close: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA).
    
    SMA is the arithmetic mean of prices over a specified number of periods.
    
    Args:
        close: Series of closing prices
        period: Number of periods for the moving average
        
    Returns:
        pd.Series: SMA values
        
    Example:
        >>> sma_50 = calculate_sma(close, period=50)
    """
    try:
        sma = close.rolling(window=period, min_periods=period).mean()
        logger.debug(f"SMA calculated with period={period}")
        return sma
        
    except Exception as e:
        logger.error(f"Error calculating SMA (period={period}): {str(e)}")
        return pd.Series(np.nan, index=close.index)


def calculate_bollinger_bands(
    close: pd.Series,
    period: int = 20,
    std_dev: int = 2
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Bollinger Bands consist of a middle band (SMA) and two outer bands
    (standard deviations above and below the middle band).
    
    Args:
        close: Series of closing prices
        period: Rolling window period (default: 20)
        std_dev: Number of standard deviations (default: 2)
        
    Returns:
        Tuple of (upper_band, lower_band, middle_band)
        
    Example:
        >>> upper, lower, middle = calculate_bollinger_bands(close)
    """
    try:
        # Middle band (SMA)
        middle_band = close.rolling(window=period, min_periods=period).mean()
        
        # Standard deviation
        rolling_std = close.rolling(window=period, min_periods=period).std()
        
        # Upper and lower bands
        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)
        
        logger.debug(f"Bollinger Bands calculated with period={period}, std_dev={std_dev}")
        return upper_band, lower_band, middle_band
        
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands: {str(e)}")
        return (
            pd.Series(np.nan, index=close.index),
            pd.Series(np.nan, index=close.index),
            pd.Series(np.nan, index=close.index)
        )


def calculate_volume_zscore(volume: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Volume Z-Score.
    
    Z-score measures how many standard deviations the current volume
    is from the rolling mean volume.
    
    Args:
        volume: Series of trading volumes
        period: Rolling window period (default: 20)
        
    Returns:
        pd.Series: Volume Z-Score values
        
    Example:
        >>> vol_zscore = calculate_volume_zscore(volume, period=20)
    """
    try:
        rolling_mean = volume.rolling(window=period, min_periods=period).mean()
        rolling_std = volume.rolling(window=period, min_periods=period).std()
        
        # Calculate Z-score
        vol_zscore = (volume - rolling_mean) / rolling_std.replace(0, np.nan)
        
        logger.debug(f"Volume Z-Score calculated with period={period}")
        return vol_zscore
        
    except Exception as e:
        logger.error(f"Error calculating Volume Z-Score: {str(e)}")
        return pd.Series(np.nan, index=volume.index)


def calculate_volatility(daily_return: pd.Series, period: int = 20) -> pd.Series:
    """
    Calculate Rolling Volatility.
    
    Volatility is measured as the rolling standard deviation of daily returns,
    annualized by multiplying by sqrt(252) trading days.
    
    Args:
        daily_return: Series of daily percentage returns
        period: Rolling window period (default: 20)
        
    Returns:
        pd.Series: Annualized volatility values
        
    Example:
        >>> volatility = calculate_volatility(daily_returns, period=20)
    """
    try:
        # Calculate rolling std and annualize
        volatility = daily_return.rolling(window=period, min_periods=period).std() * np.sqrt(252)
        
        logger.debug(f"Volatility calculated with period={period}")
        return volatility
        
    except Exception as e:
        logger.error(f"Error calculating Volatility: {str(e)}")
        return pd.Series(np.nan, index=daily_return.index)


def generate_signal(
    rsi: pd.Series,
    macd: pd.Series,
    macd_signal: pd.Series
) -> pd.Series:
    """
    Generate trading signals based on RSI and MACD crossovers.
    
    Signal Rules:
    - BUY: RSI < 40 (oversold) OR MACD crosses above signal line (bullish crossover)
    - SELL: RSI > 70 (overbought) OR MACD crosses below signal line (bearish crossover)
    - HOLD: Otherwise
    
    Args:
        rsi: RSI values
        macd: MACD line values
        macd_signal: MACD signal line values
        
    Returns:
        pd.Series: Trading signals ('BUY', 'SELL', or 'HOLD')
        
    Example:
        >>> signals = generate_signal(rsi, macd_line, signal_line)
    """
    try:
        # Initialize signals as HOLD
        signals = pd.Series("HOLD", index=rsi.index)
        
        # RSI-based signals
        signals[rsi < 40] = "BUY"
        signals[rsi > 70] = "SELL"
        
        # MACD crossover detection
        macd_diff = macd - macd_signal
        macd_diff_prev = macd_diff.shift(1)
        
        # Bullish crossover: MACD crosses above signal line
        bullish_crossover = (macd_diff > 0) & (macd_diff_prev <= 0)
        signals[bullish_crossover] = "BUY"
        
        # Bearish crossover: MACD crosses below signal line
        bearish_crossover = (macd_diff < 0) & (macd_diff_prev >= 0)
        signals[bearish_crossover] = "SELL"
        
        # Count signals for logging
        buy_count = (signals == "BUY").sum()
        sell_count = (signals == "SELL").sum()
        hold_count = (signals == "HOLD").sum()
        
        logger.debug(
            f"Signals generated: BUY={buy_count}, SELL={sell_count}, HOLD={hold_count}"
        )
        
        return signals
        
    except Exception as e:
        logger.error(f"Error generating signals: {str(e)}")
        return pd.Series("HOLD", index=rsi.index)
