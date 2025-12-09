"""
Core Utilities Module

This module contains core utilities used throughout the application:
- Database connection management
- General utility functions
"""

from server.core.database import (
    get_database,
    get_database_standalone
)

__all__ = [
    'get_database',
    'get_database_standalone',
]

