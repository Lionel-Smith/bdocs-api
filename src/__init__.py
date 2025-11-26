"""
Flask Backend - Async Quart Application

This package has been migrated from Flask to Quart for async/await support.

IMPORTANT: This project NOW USES QUART (not Flask)
- The legacy Flask code has been moved to __init__.py.bak
- The main async app factory is in src/app.py
- All controllers must use async def
- Database calls require await

For historical reasons, the project is still called "flask-backend" but it runs on Quart.
"""

# Package metadata
__version__ = "2.0.0"
__framework__ = "Quart"  # NOT Flask anymore!

# Re-export the Quart app factory for convenience
from src.app import create_app

__all__ = ['create_app']
