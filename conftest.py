import pytest
import asyncio
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def app():
    """Create test application"""
    from src.app import create_app
    from config import PostgresDB

    # Override for test database
    PostgresDB.database = f"{PostgresDB.database}_test"

    app = await create_app()
    app.config['TESTING'] = True

    yield app


@pytest.fixture
async def client(app):
    """Create test client"""
    return app.test_client()
