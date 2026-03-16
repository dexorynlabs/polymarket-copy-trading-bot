"""
Centralized data directory paths for the application.
All runtime data (logs, cache, results) is organized under data/ directory.
"""
from pathlib import Path

# Project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Base data directory
DATA_DIR = PROJECT_ROOT / 'data'

# Logs directory
LOGS_DIR = DATA_DIR / 'logs'

# Cache directory
CACHE_DIR = DATA_DIR / 'cache'
TRADER_DATA_CACHE_DIR = CACHE_DIR / 'trader_data'

# Results directory
RESULTS_DIR = DATA_DIR / 'results'
SIMULATION_RESULTS_DIR = RESULTS_DIR / 'simulations'
AUDIT_RESULTS_DIR = RESULTS_DIR / 'audits'
STRATEGY_RESULTS_DIR = RESULTS_DIR / 'strategies'


def ensure_directories():
    """Ensure all data directories exist"""
    directories = [
        DATA_DIR,
        LOGS_DIR,
        CACHE_DIR,
        TRADER_DATA_CACHE_DIR,
        RESULTS_DIR,
        SIMULATION_RESULTS_DIR,
        AUDIT_RESULTS_DIR,
        STRATEGY_RESULTS_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

