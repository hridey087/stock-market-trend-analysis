"""
Main Data Pipeline for Stock Market Trend Analysis.

Orchestrates the complete ETL process:
1. Fetches historical OHLCV data from yfinance for Nifty 50 stocks
2. Computes technical indicators using feature_engineering module
3. Saves processed data to CSV and optionally to PostgreSQL

Usage:
    python data_pipeline.py
"""

import os
import sys
import time
import logging
from typing import List, Dict
from datetime import datetime

import pandas as pd
import numpy as np
import yfinance as yf

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    NIFTY_50_SYMBOLS,
    SECTOR_MAP,
    START_DATE,
    END_DATE,
    logger,
)
from feature_engineering import (
    calculate_rsi,
    calculate_macd,
    calculate_sma,
    calculate_bollinger_bands,
    calculate_volume_zscore,
    calculate_volatility,
    generate_signal,
)


def fetch_stock_data(
    symbols: List[str],
    start_date: str,
    end_date: str,
    max_retries: int = 3
) -> pd.DataFrame:
    """
    Fetch historical OHLCV data from yfinance with retry logic.
    
    Args:
        symbols: List of stock symbols (NSE format, e.g., 'INFY.NS')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        max_retries: Maximum number of retry attempts (default: 3)
        
    Returns:
        pd.DataFrame: Multi-index DataFrame with OHLCV data for all symbols
    """
    logger.info(f"Fetching data for {len(symbols)} stocks from {start_date} to {end_date}")
    
    # Convert to NSE format if needed
    nse_symbols = [f"{symbol}.NS" if not symbol.endswith(".NS") else symbol for symbol in symbols]
    
    all_data = []
    failed_symbols = []
    
    for idx, symbol in enumerate(nse_symbols, 1):
        original_symbol = symbol.replace(".NS", "")
        logger.info(f"[{idx}/{len(nse_symbols)}] Fetching {original_symbol}...")
        
        for attempt in range(max_retries):
            try:
                # Fetch data with yfinance
                df = yf.download(
                    symbol,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    auto_adjust=False
                )
                
                if df.empty:
                    logger.warning(f"No data returned for {original_symbol}")
                    failed_symbols.append(original_symbol)
                    break
                
                # Flatten multi-level columns if present
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                # Add symbol column
                df['Symbol'] = original_symbol
                
                # Reset index to make Date a column
                df = df.reset_index()
                if 'Date' in df.columns:
                    df.rename(columns={'Date': 'date'}, inplace=True)
                elif 'index' in df.columns:
                    df.rename(columns={'index': 'date'}, inplace=True)
                
                all_data.append(df)
                logger.info(f"Successfully fetched {len(df)} records for {original_symbol}")
                break
                
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed for {original_symbol}: {str(e)}"
                )
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All attempts failed for {original_symbol}")
                    failed_symbols.append(original_symbol)
        
        # Rate limiting - brief pause between requests
        time.sleep(0.5)
    
    if not all_data:
        raise ValueError("No data was successfully fetched for any symbol")
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    logger.info(
        f"Data fetch complete: {len(combined_df)} total records, "
        f"{len(failed_symbols)} failed symbols: {failed_symbols}"
    )
    
    return combined_df


def add_sector_mapping(df: pd.DataFrame, sector_map: Dict[str, str]) -> pd.DataFrame:
    """
    Add sector labels to stock data based on symbol mapping.
    
    Args:
        df: DataFrame with 'symbol' column
        sector_map: Dictionary mapping symbols to sectors
        
    Returns:
        pd.DataFrame: DataFrame with added 'sector' column
    """
    logger.info("Adding sector mappings...")
    
    df['sector'] = df['symbol'].map(sector_map)
    
    # Log unmapped symbols
    unmapped = df[df['sector'].isna()]['symbol'].unique()
    if len(unmapped) > 0:
        logger.warning(f"Unmapped symbols found: {list(unmapped)}")
    
    return df


def compute_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all technical indicators for each stock.
    
    Args:
        df: DataFrame with OHLCV data and 'symbol' column
        
    Returns:
        pd.DataFrame: DataFrame with all technical indicators
    """
    logger.info("Computing technical indicators...")
    
    processed_stocks = []
    
    # Group by symbol and compute features
    for symbol, group in df.groupby('symbol'):
        # Sort by date
        group = group.sort_values('date').copy()
        
        try:
            # Daily returns
            group['daily_return'] = group['close'].pct_change()
            
            # RSI
            group['rsi_14'] = calculate_rsi(group['close'], period=14)
            
            # MACD
            macd_line, signal_line, histogram = calculate_macd(
                group['close'], fast=12, slow=26, signal=9
            )
            group['macd'] = macd_line
            group['macd_signal'] = signal_line
            group['macd_hist'] = histogram
            
            # Simple Moving Averages
            group['sma_20'] = calculate_sma(group['close'], period=20)
            group['sma_50'] = calculate_sma(group['close'], period=50)
            group['sma_200'] = calculate_sma(group['close'], period=200)
            
            # Bollinger Bands
            bb_upper, bb_lower, bb_mid = calculate_bollinger_bands(
                group['close'], period=20, std_dev=2
            )
            group['bb_upper'] = bb_upper
            group['bb_lower'] = bb_lower
            group['bb_mid'] = bb_mid
            
            # Volume Z-Score
            group['vol_zscore'] = calculate_volume_zscore(group['volume'], period=20)
            
            # Volatility (annualized)
            group['volatility_20d'] = calculate_volatility(group['daily_return'], period=20)
            
            # Trading Signals
            group['signal'] = generate_signal(
                group['rsi_14'], group['macd'], group['macd_signal']
            )
            
            processed_stocks.append(group)
            logger.debug(f"Features computed for {symbol}")
            
        except Exception as e:
            logger.error(f"Error computing features for {symbol}: {str(e)}")
            continue
    
    if not processed_stocks:
        raise ValueError("No stocks were successfully processed")
    
    result_df = pd.concat(processed_stocks, ignore_index=True)
    
    logger.info(f"Feature engineering complete: {len(result_df)} records processed")
    
    return result_df


def save_to_csv(df: pd.DataFrame, filepath: str) -> None:
    """
    Save DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        filepath: Output file path
    """
    logger.info(f"Saving data to {filepath}...")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Save to CSV
    df.to_csv(filepath, index=False)
    
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    logger.info(
        f"Data saved successfully: {len(df)} records, "
        f"{file_size_mb:.2f} MB"
    )


def main():
    """
    Main pipeline orchestration function.
    
    Executes the complete data pipeline:
    1. Fetch OHLCV data from yfinance
    2. Add sector mappings
    3. Compute technical indicators
    4. Save to CSV
    """
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info("STOCK MARKET TREND ANALYSIS - DATA PIPELINE")
    logger.info("=" * 70)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Date Range: {START_DATE} to {END_DATE}")
    logger.info(f"Symbols: {len(NIFTY_50_SYMBOLS)} stocks")
    logger.info("=" * 70)
    
    try:
        # Step 1: Fetch data
        logger.info("\n[STEP 1/4] Fetching historical data from yfinance...")
        raw_df = fetch_stock_data(NIFTY_50_SYMBOLS, START_DATE, END_DATE)
        
        # Rename columns to lowercase
        column_mapping = {
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Symbol': 'symbol',
        }
        raw_df = raw_df.rename(columns=column_mapping)
        
        # Ensure date is datetime
        raw_df['date'] = pd.to_datetime(raw_df['date'])
        
        logger.info(f"Raw data shape: {raw_df.shape}")
        
        # Step 2: Add sector mappings
        logger.info("\n[STEP 2/4] Adding sector mappings...")
        raw_df = add_sector_mapping(raw_df, SECTOR_MAP)
        
        # Step 3: Compute features
        logger.info("\n[STEP 3/4] Computing technical indicators...")
        features_df = compute_all_features(raw_df)
        
        # Step 4: Save to CSV
        logger.info("\n[STEP 4/4] Saving to CSV...")
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "nse_bse_features.csv"
        )
        save_to_csv(features_df, output_path)
        
        # Final statistics
        elapsed_time = time.time() - start_time
        logger.info("\n" + "=" * 70)
        logger.info("PIPELINE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total Records: {len(features_df)}")
        logger.info(f"Stocks Processed: {features_df['symbol'].nunique()}")
        logger.info(f"Date Range: {features_df['date'].min()} to {features_df['date'].max()}")
        logger.info(f"Elapsed Time: {elapsed_time:.2f} seconds")
        logger.info(f"Output File: {output_path}")
        logger.info("=" * 70)
        
        # Signal distribution
        signal_counts = features_df['signal'].value_counts()
        logger.info("\nSignal Distribution:")
        for signal, count in signal_counts.items():
            pct = (count / len(features_df)) * 100
            logger.info(f"  {signal}: {count} ({pct:.1f}%)")
        
        return features_df
        
    except Exception as e:
        logger.error(f"\nPipeline failed with error: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
