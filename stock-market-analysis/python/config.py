"""
Configuration module for Stock Market Trend Analysis Dashboard.

Loads environment variables, defines database connection parameters,
Nifty 50 stock symbols with sector mappings, and logging configuration.
"""

import os
import logging
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "database": os.getenv("POSTGRES_DB", "stock_analysis"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}


def get_database_url() -> str:
    """
    Construct PostgreSQL database URL from environment variables.
    
    Returns:
        str: Database URL in format postgresql://user:password@host:port/database
    """
    return (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )


# ============================================================
# DATE RANGE CONFIGURATION
# ============================================================

START_DATE = "2025-01-01"
END_DATE = "2025-04-30"


# ============================================================
# NIFTY 50 STOCK SYMBOLS WITH SECTOR MAPPINGS
# ============================================================

SECTOR_MAP: Dict[str, str] = {
    # Information Technology (6 stocks)
    "INFY": "IT",
    "TCS": "IT",
    "WIPRO": "IT",
    "HCLTECH": "IT",
    "TECHM": "IT",
    "LTIM": "IT",
    # Banking & Financial Services (7 stocks)
    "HDFCBANK": "Banking",
    "ICICIBANK": "Banking",
    "SBIN": "Banking",
    "AXISBANK": "Banking",
    "KOTAKBANK": "Banking",
    "INDUSINDBK": "Banking",
    "BAJFINANCE": "Banking",
    # FMCG (6 stocks)
    "HINDUNILVR": "FMCG",
    "ITC": "FMCG",
    "NESTLEIND": "FMCG",
    "BRITANNIA": "FMCG",
    "DABUR": "FMCG",
    "TATACONSUM": "FMCG",
    # Automobile (5 stocks)
    "TATAMOTORS": "Auto",
    "MARUTI": "Auto",
    "M&M": "Auto",
    "BAJAJ-AUTO": "Auto",
    "HEROMOTOCO": "Auto",
    # Pharmaceuticals (4 stocks)
    "SUNPHARMA": "Pharma",
    "DRREDDY": "Pharma",
    "CIPLA": "Pharma",
    "DIVISLAB": "Pharma",
    # Energy & Power (5 stocks)
    "RELIANCE": "Energy",
    "NTPC": "Energy",
    "ONGC": "Energy",
    "POWERGRID": "Energy",
    "COALINDIA": "Energy",
    # Metals & Mining (4 stocks)
    "TATASTEEL": "Metals",
    "JSWSTEEL": "Metals",
    "HINDALCO": "Metals",
    "ADANIENT": "Metals",
    # Realty & Ports (2 stocks)
    "ADANIPORTS": "Realty",
    "DLF": "Realty",
    # Infrastructure & Others (11 stocks)
    "LT": "Infra",
    "ULTRACEMCO": "Infra",
    "ASIANPAINT": "Infra",
    "TITAN": "Infra",
    "BAJAJFINSV": "Infra",
    "GRASIM": "Infra",
    "SHREECEM": "Infra",
    "PIDILITIND": "Infra",
    "SBILIFE": "Infra",
    "HDFCLIFE": "Infra",
    "HAVELLS": "Infra",
}

NIFTY_50_SYMBOLS: List[str] = list(SECTOR_MAP.keys())


# ============================================================
# LOGGING CONFIGURATION
# ============================================================

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger("stock_analysis")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # Add handler if not already added
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger


# Initialize logger
logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))
