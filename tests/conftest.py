"""
BDOCS API Test Fixtures

Provides pytest fixtures for async testing with Quart application.
"""
import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator

# Add project root to path
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, ROOT_PATH)
sys.path.insert(0, os.path.join(ROOT_PATH, 'src'))


# =============================================================================
# Event Loop Fixture
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Create a session-scoped event loop for async tests.

    This fixture is required by pytest-asyncio for session-scoped async fixtures.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Application Fixtures
# =============================================================================

@pytest.fixture(scope="session")
async def app():
    """
    Create test application instance.

    Configures the app for testing mode with a separate test database.
    """
    # Set test environment
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['POSTGRES_DB'] = os.environ.get('POSTGRES_DB', 'bdocs') + '_test'

    from src.app import create_app

    application = await create_app()
    application.config['TESTING'] = True

    yield application


@pytest.fixture
async def client(app):
    """
    Create async test client for making requests.

    Usage:
        async def test_endpoint(client):
            response = await client.get('/api/v1/health')
            assert response.status_code == 200
    """
    return app.test_client()


@pytest.fixture
async def authenticated_client(client, auth_token):
    """
    Create authenticated test client with JWT token.

    Usage:
        async def test_protected_endpoint(authenticated_client):
            response = await authenticated_client.get('/api/v1/inmates')
            assert response.status_code == 200
    """
    client.headers = {'Authorization': f'Bearer {auth_token}'}
    return client


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(scope="session")
async def db_session(app):
    """
    Create database session for tests.

    Handles transaction rollback after each test module.
    """
    from src.database import async_session_maker

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(autouse=True)
async def reset_db(db_session):
    """
    Reset database state after each test.

    Rolls back any uncommitted changes to maintain test isolation.
    """
    yield
    await db_session.rollback()


# =============================================================================
# Authentication Fixtures
# =============================================================================

@pytest.fixture
def auth_token():
    """
    Generate a valid JWT token for testing authenticated endpoints.
    """
    import jwt
    from datetime import datetime, timedelta

    secret = os.environ.get('JWT_SECRET_KEY', 'test-secret')
    payload = {
        'sub': 'test-user-id',
        'username': 'testuser',
        'role': 'admin',
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
    }
    return jwt.encode(payload, secret, algorithm='HS256')


@pytest.fixture
def test_user_data():
    """
    Provide sample user data for testing.
    """
    return {
        'id': 'test-user-id',
        'username': 'testuser',
        'email': 'test@bdocs.local',
        'role': 'admin',
        'is_active': True,
    }


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_inmate_data():
    """
    Provide sample inmate data for testing.
    """
    return {
        'first_name': 'John',
        'middle_name': 'Robert',
        'last_name': 'Doe',
        'date_of_birth': '1985-03-15',
        'gender': 'MALE',
        'nationality': 'Bahamian',
        'island_of_origin': 'New Providence',
        'height_cm': 180,
        'weight_kg': 75,
        'eye_color': 'BROWN',
        'hair_color': 'BLACK',
        'distinguishing_marks': 'Scar on left arm',
        'phone': '(242) 555-1234',
        'emergency_contact_name': 'Jane Doe',
        'emergency_contact_phone': '(242) 555-5678',
        'admission_date': '2024-01-15',
        'security_level': 'MEDIUM',
        'housing_unit_id': 'test-unit-id',
    }


@pytest.fixture
def sample_clemency_petition_data():
    """
    Provide sample clemency petition data for testing.
    """
    return {
        'inmate_id': 'test-inmate-id',
        'sentence_id': 'test-sentence-id',
        'petition_type': 'COMMUTATION',
        'grounds_for_clemency': 'Exemplary behavior and rehabilitation progress over 5 years.',
        'petitioner_name': 'Jane Doe',
        'petitioner_relationship': 'Spouse',
    }


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def mock_redis(mocker):
    """
    Mock Redis client for tests that don't need actual Redis.
    """
    mock = mocker.MagicMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    return mock


@pytest.fixture
def freeze_time(mocker):
    """
    Factory fixture to freeze time at a specific datetime.

    Usage:
        def test_with_frozen_time(freeze_time):
            with freeze_time('2024-01-15 12:00:00'):
                # Time is frozen here
                pass
    """
    from datetime import datetime
    from contextlib import contextmanager

    @contextmanager
    def _freeze(time_str):
        frozen_time = datetime.fromisoformat(time_str)
        mocker.patch('datetime.datetime').now.return_value = frozen_time
        mocker.patch('datetime.datetime').utcnow.return_value = frozen_time
        yield frozen_time

    return _freeze
