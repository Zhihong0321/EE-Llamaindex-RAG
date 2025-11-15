"""Shared pytest configuration and fixtures for all tests."""

import pytest


# Configure pytest-asyncio to use auto mode
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test"
    )
