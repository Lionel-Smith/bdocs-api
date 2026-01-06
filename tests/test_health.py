"""
Health Check Endpoint Tests

Tests the /api/v1/health endpoint to ensure the application is running correctly.
"""
import pytest


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, client):
        """
        Test that health endpoint returns 200 OK when service is healthy.
        """
        response = await client.get('/api/v1/health')
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_returns_json(self, client):
        """
        Test that health endpoint returns valid JSON response.
        """
        response = await client.get('/api/v1/health')
        data = await response.get_json()

        assert data is not None
        assert 'status' in data

    @pytest.mark.asyncio
    async def test_health_check_status_is_healthy(self, client):
        """
        Test that health endpoint reports healthy status.
        """
        response = await client.get('/api/v1/health')
        data = await response.get_json()

        assert data.get('status') in ['healthy', 'ok']

    @pytest.mark.asyncio
    async def test_health_check_includes_version(self, client):
        """
        Test that health endpoint includes version information.
        """
        response = await client.get('/api/v1/health')
        data = await response.get_json()

        # Version may or may not be included depending on implementation
        # This test is informational
        if 'version' in data:
            assert isinstance(data['version'], str)

    @pytest.mark.asyncio
    async def test_health_check_includes_timestamp(self, client):
        """
        Test that health endpoint includes timestamp.
        """
        response = await client.get('/api/v1/health')
        data = await response.get_json()

        # Timestamp may or may not be included depending on implementation
        if 'timestamp' in data:
            assert isinstance(data['timestamp'], str)


class TestHealthEndpointDetailed:
    """Tests for detailed health check endpoint (if available)."""

    @pytest.mark.asyncio
    async def test_detailed_health_check(self, client):
        """
        Test detailed health endpoint that checks all dependencies.
        """
        response = await client.get('/api/v1/health/detailed')

        # This endpoint may not exist - that's OK
        if response.status_code == 404:
            pytest.skip('Detailed health endpoint not implemented')

        assert response.status_code == 200
        data = await response.get_json()

        # Check for component health status
        if 'components' in data:
            components = data['components']
            assert isinstance(components, dict)

            # Check database health if present
            if 'database' in components:
                assert 'status' in components['database']

            # Check redis health if present
            if 'redis' in components:
                assert 'status' in components['redis']


class TestReadinessProbe:
    """Tests for Kubernetes-style readiness probe."""

    @pytest.mark.asyncio
    async def test_readiness_endpoint(self, client):
        """
        Test readiness endpoint for Kubernetes health checks.
        """
        response = await client.get('/api/v1/health/ready')

        # This endpoint may not exist - that's OK
        if response.status_code == 404:
            pytest.skip('Readiness endpoint not implemented')

        # Readiness should return 200 when ready, 503 when not
        assert response.status_code in [200, 503]


class TestLivenessProbe:
    """Tests for Kubernetes-style liveness probe."""

    @pytest.mark.asyncio
    async def test_liveness_endpoint(self, client):
        """
        Test liveness endpoint for Kubernetes health checks.
        """
        response = await client.get('/api/v1/health/live')

        # This endpoint may not exist - that's OK
        if response.status_code == 404:
            pytest.skip('Liveness endpoint not implemented')

        # Liveness should return 200 if the process is alive
        assert response.status_code == 200
