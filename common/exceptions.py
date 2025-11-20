"""
Custom exceptions for the auto-deploy project.
"""


class DeployException(Exception):
    """Base exception for all deployment-related errors."""
    pass


class ConfigException(DeployException):
    """Exception raised for configuration errors."""
    pass


class ConnectionException(DeployException):
    """Exception raised for SSH connection errors."""
    pass


class CheckException(DeployException):
    """Exception raised for pre-installation check failures."""
    pass


class InstallException(DeployException):
    """Exception raised for installation errors."""
    pass


class AnsibleException(DeployException):
    """Exception raised for Ansible execution errors."""
    pass
