"""
Configuration settings for the options trading engine
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Polygon.io Configuration
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
POLYGON_BASE_URL = "https://api.polygon.io"

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# API Server Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Data Configuration
DATA_PROVIDER = os.getenv("DATA_PROVIDER", "polygon")  # polygon, quantconnect, mock
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))

# Options Screening Configuration
SCREENING_CONFIG = {
    "min_volume": 100,
    "min_open_interest": 50,
    "iv_percentile_range": (10, 90),
    "default_dte_range": (7, 60),  # Days to expiration
}

# Strategy Configuration
STRATEGY_CONFIG = {
    "iron_condor": {
        "min_probability": 0.50,
        "min_return_on_risk": 0.10,
    },
    "bull_call_spread": {
        "min_probability": 0.55,
        "min_return_on_risk": 0.15,
    },
    "long_straddle": {
        "min_probability": 0.45,
        "min_return_on_risk": 0.20,
    },
}

# Logging Configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
