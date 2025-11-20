"""
Test configuration and fixtures for auto-deploy tests.
"""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / 'fixtures'


@pytest.fixture
def sample_config_file(test_data_dir):
    """Return path to sample config file."""
    return test_data_dir / 'test_config.yml'


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create temporary log directory."""
    log_dir = tmp_path / 'logs'
    log_dir.mkdir()
    return log_dir
