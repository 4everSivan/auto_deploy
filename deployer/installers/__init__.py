"""
Software installers package.
"""

from deployer.installers.base import BaseInstaller
from deployer.installers.java_installer import JavaInstaller
from deployer.installers.python_installer import PythonInstaller
from deployer.installers.zookeeper_installer import ZookeeperInstaller
from typing import Any

__all__ = [
    'BaseInstaller',
    'JavaInstaller',
    'PythonInstaller',
    'ZookeeperInstaller'
]


# Installer registry
INSTALLER_REGISTRY = {
    'java': JavaInstaller,
    'python': PythonInstaller,
    'zookeeper': ZookeeperInstaller
}


def get_installer(software_name: str) -> Any:
    """
    Get installer class for software.
    
    Args:
        software_name: Name of the software
        
    Returns:
        Installer class
        
    Raises:
        ValueError: If installer not found
    """
    name_lower = software_name.lower()
    if name_lower not in INSTALLER_REGISTRY:
        raise ValueError(f"No installer found for: {software_name}")
    
    return INSTALLER_REGISTRY[name_lower]
