"""
Flask REST API for Stock Market Trend Analysis Dashboard.

Provides endpoints for:
- Latest stock data
- Trading signals
- Sector summaries
- Individual stock history
- Health check

Usage:
    python flask_api.py
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from config import get_database_url, logger

# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database connection
engine: Optional[Engine] = None


def get_db_engine() -> Engine:
    """Get or create database engine."""
    global engine
    if engine is None:
        engine = create_engine(
            get_database_url(),
            pool_size=5,
            max_overflow=10,
            pool_timeout=30
        )
    return engine


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns API status and database connectivity.
    """
    try:
        db_engine = get_db_engine()
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'version': '1.0.0'
    })


@app.route('/api/latest', methods=['GET'])
def get_latest_data():
    """
    Get latest trading data for all stocks.
    
    Query Parameters:
        date: Specific date (YYYY-MM-DD), defaults to latest
        
    Returns:
        JSON: Latest OHLCV and features for all stocks
    """
    try:
        db_engine = get_db_engine()
        
        # Get latest date if not specified
        target_date = request.args.get('date')
        
        if target_date:
            query = text("""
                SELECT * FROM equity_features
                WHERE date = :target_date
                ORDER BY symbol
            """)
        else:
            query = text("""
                SELECT * FROM equity_features
                WHERE date = (SELECT MAX(date) FROM equity_features)
                ORDER BY symbol
            """)
        
        with db_engine.connect() as conn:
            result = conn.execute(query, {'target_date': target_date} if target_date else {})
            rows = [dict(row) for row in result]
        
        # Convert datetime objects to strings
        for row in rows:
            for key, value in row.items():
                if isinstance(value, (datetime,)):
                    row[key] = value.isoformat()
        
        return jsonify({
            'status': 'success',
            'count': len(rows),
            'data': rows
        })
        
    except Exception as e:
        logger.error(f"Error in /api/latest: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/signals', methods=['GET'])
def get_signals():
    """
    Get trading signals (BUY/SELL) with optional filters.
    
    Query Parameters:
        signal: Filter by signal type (BUY, SELL, HOLD)
        date: Filter by specific date (YYYY-MM-DD)
        sector: Filter by sector
        page: Page number (default: 1)
        per_page: Records per page (default: 50, max: 200)
        
    Returns:
        JSON: Filtered trading signals with pagination
    """
    try:
        db_engine = get_db_engine()
        
        # Get query parameters
        signal_filter = request.args.get('signal')
        date_filter = request.args.get('date')
        sector_filter = request.args.get('sector')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 200)
        offset = (page - 1) * per_page
        
        # Build query
        conditions = []
        params = {}
        
        if signal_filter:
            conditions.append("signal = :signal")
            params['signal'] = signal_filter.upper()
        
        if date_filter:
            conditions.append("date = :date")
            params['date'] = date_filter
        
        if sector_filter:
            conditions.append("sector = :sector")
            params['sector'] = sector_filter
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Count query
        count_query = text(f"""
            SELECT COUNT(*) FROM equity_features
            WHERE {where_clause}
        """)
        
        # Data query
        data_query = text(f"""
            SELECT date, symbol, sector, close, rsi_14, macd, macd_signal, 
                   macd_hist, signal, daily_return, volatility_20d
            FROM equity_features
            WHERE {where_clause}
            ORDER BY date DESC, symbol
            LIMIT :limit OFFSET :offset
        """)
        params['limit'] = per_page
        params['offset'] = offset
        
        with db_engine.connect() as conn:
            total_count = conn.execute(count_query, params).scalar()
            result = conn.execute(data_query, params)
            rows = [dict(row) for row in result]
        
        # Convert datetime objects
        for row in rows:
            for key, value in row.items():
                if isinstance(value, (datetime,)):
                    row[key] = value.isoformat()
        
        return jsonify({
            'status': 'success',
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            },
            'data': rows
        })
        
    except Exception as e:
        logger.error(f"Error in /api/signals: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sector-summary', methods=['GET'])
def get_sector_summary():
    """
    Get aggregated sector-level metrics.
    
    Query Parameters:
        date: Specific date (YYYY-MM-DD), defaults to latest
        
    Returns:
        JSON: Sector-wise aggregated statistics
    """
    try:
        db_engine = get_db_engine()
        
        target_date = request.args.get('date')
        
        if target_date:
            date_condition = "WHERE date = :target_date"
            params = {'target_date': target_date}
        else:
            date_condition = "WHERE date = (SELECT MAX(date) FROM equity_features)"
            params = {}
        
        query = text(f"""
            SELECT 
                sector,
                COUNT(*) AS stock_count,
                ROUND(AVG(close)::NUMERIC, 2) AS avg_close,
                ROUND(AVG(rsi_14)::NUMERIC, 2) AS avg_rsi,
                ROUND(AVG(daily_return)::NUMERIC, 6) AS avg_return,
                ROUND(AVG(volatility_20d)::NUMERIC, 6) AS avg_volatility,
                SUM(volume) AS total_volume,
                SUM(CASE WHEN signal = 'BUY' THEN 1 ELSE 0 END) AS buy_signals,
                SUM(CASE WHEN signal = 'SELL' THEN 1 ELSE 0 END) AS sell_signals,
                SUM(CASE WHEN signal = 'HOLD' THEN 1 ELSE 0 END) AS hold_signals
            FROM equity_features
            {date_condition}
            GROUP BY sector
            ORDER BY sector
        """)
        
        with db_engine.connect() as conn:
            result = conn.execute(query, params)
            rows = [dict(row) for row in result]
        
        return jsonify({
            'status': 'success',
            'count': len(rows),
            'data': rows
        })
        
    except Exception as e:
        logger.error(f"Error in /api/sector-summary: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_history(symbol: str):
    """
    Get historical data for a specific stock.
    
    Path Parameters:
        symbol: Stock symbol (e.g., INFY, TCS)
        
    Query Parameters:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Maximum records (default: 100)
        
    Returns:
        JSON: Historical OHLCV and features for the stock
    """
    try:
        db_engine = get_db_engine()
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        
        conditions = ["symbol = :symbol"]
        params = {'symbol': symbol.upper(), 'limit': limit}
        
        if start_date:
            conditions.append("date >= :start_date")
            params['start_date'] = start_date
        
        if end_date:
            conditions.append("date <= :end_date")
            params['end_date'] = end_date
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT * FROM equity_features
            WHERE {where_clause}
            ORDER BY date DESC
            LIMIT :limit
        """)
        
        with db_engine.connect() as conn:
            result = conn.execute(query, params)
            rows = [dict(row) for row in result]
        
        if not rows:
            return jsonify({
                'status': 'error',
                'message': f'No data found for symbol: {symbol}'
            }), 404
        
        # Convert datetime objects
        for row in rows:
            for key, value in row.items():
                if isinstance(value, (datetime,)):
                    row[key] = value.isoformat()
        
        return jsonify({
            'status': 'success',
            'symbol': symbol.upper(),
            'count': len(rows),
            'data': rows
        })
        
    except Exception as e:
        logger.error(f"Error in /api/stock/{symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == '__main__':
    logger.info("Starting Flask API server...")
    logger.info("Endpoints:")
    logger.info("  GET /api/health")
    logger.info("  GET /api/latest")
    logger.info("  GET /api/signals")
    logger.info("  GET /api/sector-summary")
    logger.info("  GET /api/stock/<symbol>")
    
    # Run Flask app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
