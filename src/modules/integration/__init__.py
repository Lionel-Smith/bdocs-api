"""
BDOCS External Integration Module - RBPF and external system connectivity.

This module handles integration with external systems, primarily the
Royal Bahamas Police Force (RBPF) for criminal justice data sharing.

NOTE: This is a STUB IMPLEMENTATION. All RBPF client methods return
mock data for development and testing. TODO comments throughout the
code mark where real integration would connect.

Core entity:
- ExternalSystemLog: Audit trail of all external API requests

RBPF Integration Points:
- lookup_person(nib_number): Criminal history lookup
- check_warrants(name, dob): Active warrant check
- notify_booking(inmate_data): New booking notification
- notify_release(inmate_data): Release notification

Key features:
- Complete audit logging of all external requests
- Retry logic with exponential backoff
- Health monitoring and metrics
- Correlation IDs for request tracking

Environment Variables (stubbed):
- RBPF_API_URL: Base URL for RBPF API
- RBPF_API_KEY: Authentication key
- RBPF_TIMEOUT: Request timeout in seconds

TODO: When real RBPF API becomes available:
1. Update rbpf_client.py with actual HTTP calls
2. Configure environment variables
3. Test with RBPF sandbox environment
4. Update error handling for actual API responses
"""
from src.modules.integration.models import ExternalSystemLog
from src.modules.integration.rbpf_client import RBPFClient, get_rbpf_client
from src.modules.integration.controller import integration_bp, blueprint

__all__ = [
    'ExternalSystemLog',
    'RBPFClient',
    'get_rbpf_client',
    'integration_bp',
    'blueprint'
]
