-- ============================================================
-- Stock Market Trend Analysis - PostgreSQL Schema
-- ============================================================
-- This script creates the database schema for storing
-- raw equity data and engineered features.
-- ============================================================

-- ============================================================
-- TABLE: equity_raw (Raw OHLCV Data)
-- ============================================================

CREATE TABLE IF NOT EXISTS equity_raw (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    sector VARCHAR(50),
    open NUMERIC(12, 4),
    high NUMERIC(12, 4),
    low NUMERIC(12, 4),
    close NUMERIC(12, 4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_date_symbol_raw UNIQUE (date, symbol)
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_equity_raw_date_symbol 
    ON equity_raw (date, symbol);

CREATE INDEX IF NOT EXISTS idx_equity_raw_sector 
    ON equity_raw (sector);

CREATE INDEX IF NOT EXISTS idx_equity_raw_date 
    ON equity_raw (date DESC);


-- ============================================================
-- TABLE: equity_features (Engineered Technical Indicators)
-- ============================================================

CREATE TABLE IF NOT EXISTS equity_features (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    sector VARCHAR(50),
    open NUMERIC(12, 4),
    high NUMERIC(12, 4),
    low NUMERIC(12, 4),
    close NUMERIC(12, 4),
    volume BIGINT,
    
    -- Technical Indicators
    rsi_14 NUMERIC(10, 4),
    macd NUMERIC(12, 6),
    macd_signal NUMERIC(12, 6),
    macd_hist NUMERIC(12, 6),
    sma_20 NUMERIC(12, 4),
    sma_50 NUMERIC(12, 4),
    sma_200 NUMERIC(12, 4),
    bb_upper NUMERIC(12, 4),
    bb_lower NUMERIC(12, 4),
    bb_mid NUMERIC(12, 4),
    vol_zscore NUMERIC(10, 4),
    daily_return NUMERIC(10, 6),
    volatility_20d NUMERIC(10, 6),
    
    -- Trading Signal
    signal VARCHAR(10) CHECK (signal IN ('BUY', 'SELL', 'HOLD')),
    
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_date_symbol_features UNIQUE (date, symbol)
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_equity_features_date_symbol 
    ON equity_features (date, symbol);

CREATE INDEX IF NOT EXISTS idx_equity_features_sector 
    ON equity_features (sector);

CREATE INDEX IF NOT EXISTS idx_equity_features_signal 
    ON equity_features (signal);

CREATE INDEX IF NOT EXISTS idx_equity_features_date 
    ON equity_features (date DESC);

CREATE INDEX IF NOT EXISTS idx_equity_features_rsi 
    ON equity_features (rsi_14);


-- ============================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================

COMMENT ON TABLE equity_raw IS 'Raw OHLCV data ingested from NSE/BSE via yfinance';
COMMENT ON TABLE equity_features IS 'Engineered features with technical indicators and trading signals';

COMMENT ON COLUMN equity_features.rsi_14 IS 'Relative Strength Index (14-day period)';
COMMENT ON COLUMN equity_features.macd IS 'MACD Line (12, 26, 9)';
COMMENT ON COLUMN equity_features.macd_signal IS 'MACD Signal Line (9-day EMA of MACD)';
COMMENT ON COLUMN equity_features.macd_hist IS 'MACD Histogram (MACD - Signal)';
COMMENT ON COLUMN equity_features.sma_20 IS 'Simple Moving Average (20-day)';
COMMENT ON COLUMN equity_features.sma_50 IS 'Simple Moving Average (50-day)';
COMMENT ON COLUMN equity_features.sma_200 IS 'Simple Moving Average (200-day)';
COMMENT ON COLUMN equity_features.bb_upper IS 'Bollinger Band Upper (20-day, 2 std dev)';
COMMENT ON COLUMN equity_features.bb_lower IS 'Bollinger Band Lower (20-day, 2 std dev)';
COMMENT ON COLUMN equity_features.bb_mid IS 'Bollinger Band Middle (20-day SMA)';
COMMENT ON COLUMN equity_features.vol_zscore IS 'Volume Z-Score (20-day rolling)';
COMMENT ON COLUMN equity_features.daily_return IS 'Daily percentage return';
COMMENT ON COLUMN equity_features.volatility_20d IS 'Annualized volatility (20-day rolling std)';
COMMENT ON COLUMN equity_features.signal IS 'Trading signal: BUY, SELL, or HOLD';


-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- View table structure
-- \d equity_raw
-- \d equity_features

-- Check indexes
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename IN ('equity_raw', 'equity_features');

-- Row counts
-- SELECT 'equity_raw' AS table_name, COUNT(*) FROM equity_raw
-- UNION ALL
-- SELECT 'equity_features', COUNT(*) FROM equity_features;
