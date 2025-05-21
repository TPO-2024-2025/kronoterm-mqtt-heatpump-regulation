"""Global config for pytest."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations) -> None:
    """Enable custom integrations for all tests."""
    yield
