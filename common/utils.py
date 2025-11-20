"""
Utility functions for the auto-deploy project.
"""

import os
import re
from typing import Optional, Dict, Any
from pathlib import Path


def expand_path(path: str) -> str:
    """
    Expand user home directory and environment variables in path.
    
    Args:
        path: Path string that may contain ~ or environment variables
        
    Returns:
        Expanded absolute path
    """
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def validate_port(port: int) -> bool:
    """
    Validate if port number is in valid range.
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 1 <= port <= 65535


def validate_ip(ip: str) -> bool:
    """
    Validate if string is a valid IPv4 address.
    
    Args:
        ip: IP address string
        
    Returns:
        True if valid IPv4, False otherwise
    """
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    
    parts = ip.split('.')
    return all(0 <= int(part) <= 255 for part in parts)


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human-readable string.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def sanitize_log_message(message: str, mask_patterns: Optional[list] = None) -> str:
    """
    Sanitize log message by masking sensitive information.
    
    Args:
        message: Original log message
        mask_patterns: List of regex patterns to mask (default: passwords)
        
    Returns:
        Sanitized message
    """
    if mask_patterns is None:
        mask_patterns = [
            r'(password["\']?\s*[:=]\s*["\']?)([^"\'}\s]+)',
            r'(pass["\']?\s*[:=]\s*["\']?)([^"\'}\s]+)',
            r'(secret["\']?\s*[:=]\s*["\']?)([^"\'}\s]+)',
        ]
    
    sanitized = message
    for pattern in mask_patterns:
        sanitized = re.sub(pattern, r'\1***MASKED***', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def ensure_dir(directory: str) -> Path:
    """
    Ensure directory exists, create if not.
    
    Args:
        directory: Directory path
        
    Returns:
        Path object
        
    Raises:
        PermissionError: If directory cannot be created
    """
    path = Path(expand_path(directory))
    path.mkdir(parents=True, exist_ok=True)
    return path


def check_file_permissions(file_path: str, required_mode: int = 0o600) -> bool:
    """
    Check if file has required permissions.
    
    Args:
        file_path: Path to file
        required_mode: Required permission mode (default: 0o600)
        
    Returns:
        True if permissions match, False otherwise
    """
    if not os.path.exists(file_path):
        return False
    
    current_mode = os.stat(file_path).st_mode & 0o777
    return current_mode == required_mode
