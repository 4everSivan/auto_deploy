"""
Tests for common.utils module.
"""

import pytest
import os
from common.utils import (
    expand_path,
    validate_port,
    validate_ip,
    format_bytes,
    format_duration,
    sanitize_log_message,
    ensure_dir,
    check_file_permissions
)


class TestPathUtils:
    """Tests for path utility functions."""
    
    def test_expand_path_with_home(self):
        """Test path expansion with home directory."""
        result = expand_path("~/test")
        assert os.path.isabs(result)
        assert "~" not in result
    
    def test_expand_path_with_env_var(self, monkeypatch):
        """Test path expansion with environment variable."""
        monkeypatch.setenv("TEST_VAR", "/tmp/test")
        result = expand_path("$TEST_VAR/file")
        assert "/tmp/test/file" in result


class TestValidation:
    """Tests for validation functions."""
    
    def test_validate_port_valid(self):
        """Test valid port numbers."""
        assert validate_port(22) is True
        assert validate_port(80) is True
        assert validate_port(65535) is True
    
    def test_validate_port_invalid(self):
        """Test invalid port numbers."""
        assert validate_port(0) is False
        assert validate_port(-1) is False
        assert validate_port(65536) is False
    
    def test_validate_ip_valid(self):
        """Test valid IP addresses."""
        assert validate_ip("192.168.1.1") is True
        assert validate_ip("10.0.0.1") is True
        assert validate_ip("255.255.255.255") is True
    
    def test_validate_ip_invalid(self):
        """Test invalid IP addresses."""
        assert validate_ip("256.1.1.1") is False
        assert validate_ip("192.168.1") is False
        assert validate_ip("not.an.ip.address") is False


class TestFormatting:
    """Tests for formatting functions."""
    
    def test_format_bytes(self):
        """Test bytes formatting."""
        assert format_bytes(0) == "0.0 B"
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1024 * 1024) == "1.0 MB"
        assert format_bytes(1024 * 1024 * 1024) == "1.0 GB"
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(0) == "0s"
        assert format_duration(45) == "45s"
        assert format_duration(90) == "1m 30s"
        assert format_duration(3661) == "1h 1m 1s"


class TestSanitization:
    """Tests for log sanitization."""
    
    def test_sanitize_password(self):
        """Test password sanitization."""
        message = 'password: "secret123"'
        result = sanitize_log_message(message)
        assert "secret123" not in result
        assert "***MASKED***" in result
    
    def test_sanitize_pass(self):
        """Test pass field sanitization."""
        message = "pass=mypassword"
        result = sanitize_log_message(message)
        assert "mypassword" not in result
        assert "***MASKED***" in result
    
    def test_sanitize_no_sensitive_data(self):
        """Test message without sensitive data."""
        message = "Installing Java on node_01"
        result = sanitize_log_message(message)
        assert result == message


class TestFileOperations:
    """Tests for file operation utilities."""
    
    def test_ensure_dir_creates_directory(self, tmp_path):
        """Test directory creation."""
        test_dir = tmp_path / "test" / "nested" / "dir"
        result = ensure_dir(str(test_dir))
        assert result.exists()
        assert result.is_dir()
    
    def test_ensure_dir_existing_directory(self, tmp_path):
        """Test with existing directory."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()
        result = ensure_dir(str(test_dir))
        assert result.exists()
    
    def test_check_file_permissions(self, tmp_path):
        """Test file permission checking."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        os.chmod(test_file, 0o600)
        assert check_file_permissions(str(test_file), 0o600) is True
        assert check_file_permissions(str(test_file), 0o644) is False
