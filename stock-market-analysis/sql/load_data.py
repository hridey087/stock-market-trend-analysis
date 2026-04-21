"""
Data Loader for PostgreSQL Database.

Loads CSV data into PostgreSQL with upsert logic using SQLAlchemy.
Supports batch insertion for performance optimization.

Usage:
    python load_data.py
"""

import os
import sys
import logging
from typing import Tuple
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from config import get_database_url, logger


def create_engine_from_env() -> Engine:
    """
    Create SQLAlchemy engine from environment variables.
    
    Returns:
        Engine: SQLAlchemy engine instance
        
    Raises:
        ValueError: If database URL is not properly configured
    """
    db_url = get_database_url()
    
    if not db_url:
        raise ValueError("Database URL not configured. Check your .env file.")
    
    logger.info(f"Connecting to database: {db_url.split('@')[1] if '@' in db_url else 'N/A'}")
    
    engine = create_engine(
        db_url,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800
    )
    
    return engine


def load_raw_data(df: pd.DataFrame, engine: Engine) -> int:
    """
    Load raw OHLCV data into equity_raw table.
    
    Args:
        df: DataFrame with raw stock data
        engine: SQLAlchemy engine instance
        
    Returns:
        int: Number of rows inserted/updated
    """
    logger.info("Loading raw data into equity_raw table...")
    
    # Select only raw data columns
    raw_columns = ['date', 'symbol', 'sector', 'open', 'high', 'low', 'close', 'volume']
    raw_df = df[raw_columns].copy()
    
    # Convert date to datetime
    raw_df['date'] = pd.to_datetime(raw_df['date'])
    
    # Upsert data
    rows_affected = upsert_dataframe(raw_df, 'equity_raw', engine)
    
    logger.info(f"Raw data loaded: {rows_affected} rows")
    return rows_affected


def load_features_data(df: pd.DataFrame, engine: Engine) -> int:
    """
    Load engineered features into equity_features table.
    
    Args:
        df: DataFrame with all features
        engine: SQLAlchemy engine instance
        
    Returns:
        int: Number of rows inserted/updated
    """
    logger.info("Loading features data into equity_features table...")
    
    # Select all feature columns
    feature_columns = [
        'date', 'symbol', 'sector', 'open', 'high', 'low', 'close', 'volume',
        'rsi_14', 'macd', 'macd_signal', 'macd_hist',
        'sma_20', 'sma_50', 'sma_200',
        'bb_upper', 'bb_lower', 'bb_mid',
        'vol_zscore', 'daily_return', 'volatility_20d', 'signal'
    ]
    features_df = df[feature_columns].copy()
    
    # Convert date to datetime
    features_df['date'] = pd.to_datetime(features_df['date'])
    
    # Replace NaN with None for SQL compatibility
    features_df = features_df.replace({float('nan'): None})
    
    # Upsert data
    rows_affected = upsert_dataframe(features_df, 'equity_features', engine)
    
    logger.info(f"Features data loaded: {rows_affected} rows")
    return rows_affected


def upsert_dataframe(df: pd.DataFrame, table: str, engine: Engine, batch_size: int = 1000) -> int:
    """
    Upsert DataFrame into PostgreSQL table using INSERT ... ON CONFLICT.
    
    Args:
        df: DataFrame to upsert
        table: Target table name
        engine: SQLAlchemy engine instance
        batch_size: Number of rows per batch (default: 1000)
        
    Returns:
        int: Total number of rows inserted/updated
    """
    logger.info(f"Upserting {len(df)} rows to {table} (batch_size={batch_size})...")
    
    total_rows = 0
    
    # Split DataFrame into batches
    batches = [df[i:i + batch_size] for i in range(0, len(df), batch_size)]
    
    with engine.begin() as conn:
        for batch_idx, batch_df in enumerate(batches, 1):
            try:
                # Convert DataFrame to list of dictionaries
                records = batch_df.to_dict(orient='records')
                
                # Build upsert query dynamically
                columns = ', '.join(records[0].keys())
                values_placeholders = ', '.join([f':{col}' for col in records[0].keys()])
                
                # Build UPDATE clause for ON CONFLICT
                update_columns = ', '.join([
                    f"{col} = EXCLUDED.{col}" 
                    for col in records[0].keys() 
                    if col not in ['date', 'symbol']
                ])
                
                upsert_query = text(f"""
                    INSERT INTO {table} ({columns})
                    VALUES ({values_placeholders})
                    ON CONFLICT (date, symbol)
                    DO UPDATE SET {update_columns}
                """)
                
                # Execute batch upsert
                conn.execute(upsert_query, records)
                total_rows += len(batch_df)
                
                logger.debug(
                    f"Batch {batch_idx}/{len(batches)} completed: "
                    f"{len(batch_df)} rows"
                )
                
            except Exception as e:
                logger.error(f"Error in batch {batch_idx}: {str(e)}")
                raise
    
    logger.info(f"Upsert complete: {total_rows} rows processed")
    return total_rows


def verify_load(engine: Engine) -> None:
    """
    Verify data load by checking row counts and sample data.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    logger.info("Verifying data load...")
    
    with engine.connect() as conn:
        # Check row counts
        for table in ['equity_raw', 'equity_features']:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            logger.info(f"{table}: {count} rows")
        
        # Check date range
        result = conn.execute(text("""
            SELECT 
                MIN(date) AS min_date,
                MAX(date) AS max_date,
                COUNT(DISTINCT symbol) AS unique_symbols
            FROM equity_features
        """))
        row = result.fetchone()
        if row:
            logger.info(f"Date range: {row[0]} to {row[1]}")
            logger.info(f"Unique symbols: {row[2]}")
        
        # Check signal distribution
        result = conn.execute(text("""
            SELECT signal, COUNT(*) 
            FROM equity_features 
            GROUP BY signal
        """))
        logger.info("Signal distribution:")
        for row in result.fetchall():
            logger.info(f"  {row[0]}: {row[1]}")


def main():
    """
    Main function to orchestrate data loading.
    
    Reads CSV file and loads data into PostgreSQL tables.
    """
    start_time = datetime.now()
    
    logger.info("=" * 70)
    logger.info("DATA LOADER - PostgreSQL")
    logger.info("=" * 70)
    logger.info(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Create database engine
        engine = create_engine_from_env()
        
        # Read CSV file
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "nse_bse_features.csv"
        )
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        logger.info(f"Reading CSV: {csv_path}")
        df = pd.read_csv(csv_path)
        logger.info(f"CSV loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Load raw data
        raw_count = load_raw_data(df, engine)
        
        # Load features data
        features_count = load_features_data(df, engine)
        
        # Verify load
        verify_load(engine)
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("\n" + "=" * 70)
        logger.info("DATA LOAD COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Raw records: {raw_count}")
        logger.info(f"Feature records: {features_count}")
        logger.info(f"Elapsed time: {elapsed:.2f} seconds")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"\nData load failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
