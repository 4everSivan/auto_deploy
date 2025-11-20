"""
Tests for common.exceptions module.
"""

import pytest
from common.exceptions import (
    DeployException,
    ConfigException,
    ConnectionException,
    CheckException,
    InstallException,
    AnsibleException
)


def test_deploy_exception():
    """Test base DeployException."""
    exc = DeployException("Test error")
    assert str(exc) == "Test error"
    assert isinstance(exc, Exception)


def test_config_exception():
    """Test ConfigException inheritance."""
    exc = ConfigException("Config error")
    assert isinstance(exc, DeployException)
    assert str(exc) == "Config error"


def test_connection_exception():
    """Test ConnectionException inheritance."""
    exc = ConnectionException("Connection failed")
    assert isinstance(exc, DeployException)


def test_check_exception():
    """Test CheckException inheritance."""
    exc = CheckException("Check failed")
    assert isinstance(exc, DeployException)


def test_install_exception():
    """Test InstallException inheritance."""
    exc = InstallException("Install failed")
    assert isinstance(exc, DeployException)


def test_ansible_exception():
    """Test AnsibleException inheritance."""
    exc = AnsibleException("Ansible failed")
    assert isinstance(exc, DeployException)
