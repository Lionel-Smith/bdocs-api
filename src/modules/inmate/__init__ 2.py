"""
BDOCS Inmate Module - Intake and Booking Management

This module handles inmate registration, booking, and record management
for the Bahamas Department of Correctional Services.
"""
from src.modules.inmate.models import Inmate
from src.modules.inmate.controller import blueprint

__all__ = ['Inmate', 'blueprint']
