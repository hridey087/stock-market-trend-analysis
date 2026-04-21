-- ============================================================
-- Stock Market Trend Analysis - Analytical Queries
-- ============================================================
-- 8 advanced analytical queries using CTEs, window functions,
-- and proper indexing for performance.
-- ============================================================


-- ============================================================
-- QUERY 1: Top 10 Stocks by Average Daily Return per Sector
-- ============================================================
-- Uses CTE with AVG() and RANK() window function to identify
-- best-performing stocks within each sector.

WITH sector_returns AS (
    SELECT 
        symbol,
        sector,
        AVG(daily_return) AS avg_daily_return,
        COUNT(*) AS trading_days,
        STDDEV(daily_return) AS return_volatility
    FROM equity_features
    WHERE daily_return IS NOT NULL
    GROUP BY symbol, sector
),
ranked_stocks AS (
    SELECT 
        symbol,
        sector,
        avg_daily_return,
        trading_days,
        return_volatility,
        RANK() OVER (PARTITION BY sector ORDER BY avg_daily_return DESC) AS rank_in_sector
    FROM sector_returns
)
SELECT 
    sector,
    symbol,
    ROUND(avg_daily_return::NUMERIC, 6) AS avg_daily_return,
    ROUND((avg_daily_return * 100)::NUMERIC, 4) AS avg_daily_return_pct,
    trading_days,
    ROUND(return_volatility::NUMERIC, 6) AS return_volatility,
    rank_in_sector
FROM ranked_stocks
WHERE rank_in_sector <= 10
ORDER BY sector, rank_in_sector;


-- ============================================================
-- QUERY 2: BUY/SELL/HOLD Signal Count per Sector per Month
-- ============================================================
-- Aggregates trading signals by sector and month using
-- DATE_TRUNC for temporal analysis.

SELECT 
    sector,
    DATE_TRUNC('month', date) AS month,
    signal,
    COUNT(*) AS signal_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY sector, DATE_TRUNC('month', date)))::NUMERIC, 2) AS signal_percentage
FROM equity_features
WHERE signal IS NOT NULL
GROUP BY sector, DATE_TRUNC('month', date), signal
ORDER BY sector, month, signal_count DESC;


-- ============================================================
-- QUERY 3: Sector-wise Average RSI and MACD Histogram
-- ============================================================
-- Computes sector-level momentum indicators to identify
-- overall sector strength and trend direction.

SELECT 
    sector,
    ROUND(AVG(rsi_14)::NUMERIC, 2) AS avg_rsi,
    MIN(rsi_14) AS min_rsi,
    MAX(rsi_14) AS max_rsi,
    ROUND(AVG(macd_hist)::NUMERIC, 6) AS avg_macd_histogram,
    ROUND(AVG(macd)::NUMERIC, 6) AS avg_macd,
    COUNT(*) AS observation_count,
    CASE 
        WHEN AVG(rsi_14) > 70 THEN 'OVERBOUGHT'
        WHEN AVG(rsi_14) < 30 THEN 'OVERSOLD'
        ELSE 'NEUTRAL'
    END AS sector_momentum
FROM equity_features
WHERE rsi_14 IS NOT NULL AND macd_hist IS NOT NULL
GROUP BY sector
ORDER BY avg_rsi DESC;


-- ============================================================
-- QUERY 4: Most Volatile Stocks (Top 10 by Avg Volatility)
-- ============================================================
-- Identifies highest-risk stocks based on 20-day rolling
-- annualized volatility.

SELECT 
    symbol,
    sector,
    ROUND(AVG(volatility_20d)::NUMERIC, 6) AS avg_volatility,
    ROUND((AVG(volatility_20d) * 100)::NUMERIC, 2) AS avg_volatility_pct,
    MAX(volatility_20d) AS max_volatility,
    MIN(volatility_20d) AS min_volatility,
    ROUND(AVG(daily_return)::NUMERIC, 6) AS avg_return,
    COUNT(*) AS trading_days
FROM equity_features
WHERE volatility_20d IS NOT NULL
GROUP BY symbol, sector
ORDER BY avg_volatility DESC
LIMIT 10;


-- ============================================================
-- QUERY 5: MACD Bullish Crossovers in Last 5 Trading Days
-- ============================================================
-- Detects stocks where MACD line crossed above signal line
-- (bullish signal) using LAG() window function.

WITH macd_crossovers AS (
    SELECT 
        date,
        symbol,
        sector,
        close,
        macd,
        macd_signal,
        macd_hist,
        LAG(macd_hist) OVER (PARTITION BY symbol ORDER BY date) AS prev_macd_hist,
        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
    FROM equity_features
    WHERE macd_hist IS NOT NULL
),
bullish_signals AS (
    SELECT 
        date,
        symbol,
        sector,
        close,
        macd_hist,
        prev_macd_hist,
        CASE 
            WHEN macd_hist > 0 AND prev_macd_hist <= 0 THEN 'BULLISH_CROSSOVER'
            WHEN macd_hist < 0 AND prev_macd_hist >= 0 THEN 'BEARISH_CROSSOVER'
            ELSE 'NO_CROSSOVER'
        END AS crossover_type
    FROM macd_crossovers
    WHERE rn <= 5
)
SELECT 
    date,
    symbol,
    sector,
    close,
    ROUND(macd_hist::NUMERIC, 6) AS macd_histogram,
    ROUND(prev_macd_hist::NUMERIC, 6) AS prev_macd_histogram,
    crossover_type
FROM bullish_signals
WHERE crossover_type IN ('BULLISH_CROSSOVER', 'BEARISH_CROSSOVER')
ORDER BY date DESC, symbol;


-- ============================================================
-- QUERY 6: Nifty 50 Index-Level Aggregated Daily Metrics
-- ============================================================
-- Computes market-wide statistics by aggregating all 50 stocks
-- to create a synthetic Nifty 50 index view.

SELECT 
    date,
    COUNT(DISTINCT symbol) AS stocks_traded,
    ROUND(AVG(close)::NUMERIC, 2) AS nifty_50_avg_close,
    SUM(volume) AS total_volume,
    ROUND(AVG(daily_return)::NUMERIC, 6) AS avg_market_return,
    ROUND(STDDEV(daily_return)::NUMERIC, 6) AS market_volatility,
    SUM(CASE WHEN signal = 'BUY' THEN 1 ELSE 0 END) AS buy_signals,
    SUM(CASE WHEN signal = 'SELL' THEN 1 ELSE 0 END) AS sell_signals,
    SUM(CASE WHEN signal = 'HOLD' THEN 1 ELSE 0 END) AS hold_signals
FROM equity_features
GROUP BY date
ORDER BY date DESC;


-- ============================================================
-- QUERY 7: RSI Divergence Detection
-- ============================================================
-- Identifies stocks where price made new highs but RSI did not
-- (bearish divergence) or vice versa (bullish divergence).

WITH price_rsi_trends AS (
    SELECT 
        date,
        symbol,
        sector,
        close,
        rsi_14,
        -- Check if price is at 20-day high
        CASE 
            WHEN close = MAX(close) OVER (
                PARTITION BY symbol 
                ORDER BY date 
                ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
            ) THEN TRUE 
            ELSE FALSE 
        END AS price_new_high,
        -- Check if RSI is at 20-day high
        CASE 
            WHEN rsi_14 = MAX(rsi_14) OVER (
                PARTITION BY symbol 
                ORDER BY date 
                ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
            ) THEN TRUE 
            ELSE FALSE 
        END AS rsi_new_high,
        -- Previous price high
        MAX(close) OVER (
            PARTITION BY symbol 
            ORDER BY date 
            ROWS BETWEEN 21 PRECEDING AND 1 PRECEDING
        ) AS prev_price_high,
        -- Previous RSI high
        MAX(rsi_14) OVER (
            PARTITION BY symbol 
            ORDER BY date 
            ROWS BETWEEN 21 PRECEDING AND 1 PRECEDING
        ) AS prev_rsi_high
    FROM equity_features
    WHERE rsi_14 IS NOT NULL
)
SELECT 
    date,
    symbol,
    sector,
    ROUND(close::NUMERIC, 2) AS close_price,
    ROUND(rsi_14::NUMERIC, 2) AS rsi,
    CASE 
        WHEN price_new_high AND NOT rsi_new_high THEN 'BEARISH_DIVERGENCE'
        WHEN NOT price_new_high AND rsi_new_high THEN 'BULLISH_DIVERGENCE'
        ELSE 'NO_DIVERGENCE'
    END AS divergence_type
FROM price_rsi_trends
WHERE (price_new_high AND NOT rsi_new_high) 
   OR (NOT price_new_high AND rsi_new_high)
ORDER BY date DESC, symbol;


-- ============================================================
-- QUERY 8: Monthly Performance Summary per Sector
-- ============================================================
-- Comprehensive monthly aggregation showing returns, volatility,
-- signal distribution, and momentum metrics by sector.

SELECT 
    sector,
    DATE_TRUNC('month', date) AS month,
    
    -- Price metrics
    ROUND(AVG(close)::NUMERIC, 2) AS avg_close,
    MAX(close) AS month_high,
    MIN(close) AS month_low,
    
    -- Return metrics
    ROUND(AVG(daily_return)::NUMERIC, 6) AS avg_daily_return,
    ROUND(STDDEV(daily_return)::NUMERIC, 6) AS daily_return_std,
    ROUND((SUM(daily_return) * 100)::NUMERIC, 4) AS cumulative_return_pct,
    
    -- Volume metrics
    SUM(volume) AS total_volume,
    ROUND(AVG(volume)::NUMERIC, 0) AS avg_daily_volume,
    
    -- Technical indicators
    ROUND(AVG(rsi_14)::NUMERIC, 2) AS avg_rsi,
    ROUND(AVG(macd_hist)::NUMERIC, 6) AS avg_macd_histogram,
    ROUND(AVG(volatility_20d)::NUMERIC, 6) AS avg_volatility,
    
    -- Signal distribution
    COUNT(*) AS total_observations,
    SUM(CASE WHEN signal = 'BUY' THEN 1 ELSE 0 END) AS buy_count,
    SUM(CASE WHEN signal = 'SELL' THEN 1 ELSE 0 END) AS sell_count,
    SUM(CASE WHEN signal = 'HOLD' THEN 1 ELSE 0 END) AS hold_count,
    ROUND((SUM(CASE WHEN signal = 'BUY' THEN 1 ELSE 0 END) * 100.0 / COUNT(*))::NUMERIC, 2) AS buy_signal_pct
    
FROM equity_features
WHERE daily_return IS NOT NULL
GROUP BY sector, DATE_TRUNC('month', date)
ORDER BY sector, month;


-- ============================================================
-- BONUS QUERY: Sector Correlation Matrix (Returns)
-- ============================================================
-- Useful for portfolio diversification analysis.

SELECT 
    a.sector AS sector_a,
    b.sector AS sector_b,
    ROUND(CORR(a.avg_return, b.avg_return)::NUMERIC, 4) AS return_correlation
FROM (
    SELECT date, sector, AVG(daily_return) AS avg_return
    FROM equity_features
    WHERE daily_return IS NOT NULL
    GROUP BY date, sector
) a
JOIN (
    SELECT date, sector, AVG(daily_return) AS avg_return
    FROM equity_features
    WHERE daily_return IS NOT NULL
    GROUP BY date, sector
) b ON a.date = b.date AND a.sector < b.sector
GROUP BY a.sector, b.sector
ORDER BY return_correlation DESC;


-- ============================================================
-- BONUS QUERY: Best and Worst Trading Days by Sector
-- ============================================================

WITH daily_sector_returns AS (
    SELECT 
        date,
        sector,
        AVG(daily_return) AS sector_avg_return
    FROM equity_features
    WHERE daily_return IS NOT NULL
    GROUP BY date, sector
),
ranked_days AS (
    SELECT 
        sector,
        date,
        sector_avg_return,
        RANK() OVER (PARTITION BY sector ORDER BY sector_avg_return DESC) AS best_rank,
        RANK() OVER (PARTITION BY sector ORDER BY sector_avg_return ASC) AS worst_rank
    FROM daily_sector_returns
)
SELECT 
    sector,
    'BEST_DAY' AS day_type,
    date,
    ROUND((sector_avg_return * 100)::NUMERIC, 4) AS return_pct
FROM ranked_days
WHERE best_rank = 1
UNION ALL
SELECT 
    sector,
    'WORST_DAY' AS day_type,
    date,
    ROUND((sector_avg_return * 100)::NUMERIC, 4) AS return_pct
FROM ranked_days
WHERE worst_rank = 1
ORDER BY sector, day_type;
