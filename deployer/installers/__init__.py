"""
Software installers package.
"""

from deployer.installers.base import BaseInstaller
from deployer.installers.java_installer import JavaInstaller
from deployer.installers.python_installer import PythonInstaller
from deployer.installers.zookeeper_installer import ZookeeperInstaller

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


def get_installer(software_name: str):
    """
    Get installer class for software.
    
    Args:
        software_name: Name of software
        
    Returns:
        Installer class
        
    Raises:
        ValueError: If installer not found
    """
    installer_class = INSTALLER_REGISTRY.get(software_name.lower())
    if not installer_class:
        raise ValueError(
            f'No installer found for {software_name}. '
            f'Available: {list(INSTALLER_REGISTRY.keys())}'
        )
    return installer_class
