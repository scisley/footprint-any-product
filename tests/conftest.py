"""
Shared pytest fixtures and configuration for the transportation tool tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_nominatim_location():
    """Mock Nominatim location response"""
    location = Mock()
    location.latitude = 40.7128
    location.longitude = -74.0060
    location.raw = {
        'address': {
            'state': 'New York',
            'province': 'New York'
        }
    }
    return location

@pytest.fixture
def mock_llm_response():
    """Mock LLM coordinate response"""
    response = Mock()
    response.latitude = 40.7128
    response.longitude = -74.0060
    return response

@pytest.fixture
def reset_rate_limiter():
    """Reset the global rate limiter before each test"""
    with patch('tools.transportation.transportation._last_nominatim_call', 0):
        yield