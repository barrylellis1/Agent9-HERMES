"""
Global pytest configuration for Agent9 tests.

This file configures pytest to properly handle async tests and provides
helpers for agent testing. It automatically applies the asyncio marker
to all async test functions without requiring explicit decorators.
"""

import pytest

# Configure pytest to run all async tests
pytest_plugins = ["pytest_asyncio"]

# Auto-apply asyncio marker to all async test functions
def pytest_collection_modifyitems(items):
    """
    Add asyncio marker to all async test functions.
    This allows async tests to run without explicit @pytest.mark.asyncio decorators.
    """
    for item in items:
        if "async def" in item.function.__code__.co_code.__str__():
            item.add_marker(pytest.mark.asyncio)
