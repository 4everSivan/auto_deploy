"""
Configuration data classes for node and software configurations.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import os

from common.utils import expand_path, validate_port, check_file_permissions
from common.exceptions import ConfigException


@dataclass
class SoftwareConfig:
    """Software installation configuration."""
    
    name: str
    version: str
    install_path: str
    source: str = 'repository'  # local/url/repository
    source_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name:
            raise ConfigException("Software name is required")
        if not self.version:
            raise ConfigException(f"Version is required for {self.name}")
        if not self.install_path:
            raise ConfigException(f"Install path is required for {self.name}")
        
        # Expand install path
        self.install_path = expand_path(self.install_path)
        
        # Validate source
        if self.source not in ['local', 'url', 'repository']:
            raise ConfigException(
                f"Invalid source '{self.source}' for {self.name}. "
                f"Must be one of: local, url, repository"
            )
        
        # Validate source_path if source is local or url
        if self.source in ['local', 'url'] and not self.source_path:
            raise ConfigException(
                f"source_path is required when source is '{self.source}' for {self.name}"
            )
        
        # Expand source_path if it's a local file
        if self.source == 'local' and self.source_path:
            self.source_path = expand_path(self.source_path)
            if not os.path.exists(self.source_path):
                raise ConfigException(
                    f"Source file not found: {self.source_path} for {self.name}"
                )


@dataclass
class NodeConfig:
    """Node connection and deployment configuration."""
    
    name: str
    host: str
    port: int = 22
    owner_user: str = ''
    owner_pass: Optional[str] = None
    owner_key: Optional[str] = None
    super_user: str = 'root'
    super_pass: Optional[str] = None
    super_key: Optional[str] = None
    install: List[SoftwareConfig] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate required fields
        if not self.name:
            raise ConfigException("Node name is required")
        if not self.host:
            raise ConfigException(f"Host is required for node {self.name}")
        
        # Validate port
        if not validate_port(self.port):
            raise ConfigException(
                f"Invalid port {self.port} for node {self.name}. "
                f"Port must be between 1 and 65535"
            )
        
        # Validate owner user credentials
        if not self.owner_user:
            raise ConfigException(f"owner_user is required for node {self.name}")
        
        if not self.owner_pass and not self.owner_key:
            raise ConfigException(
                f"Either owner_pass or owner_key must be provided for node {self.name}"
            )
        
        # Validate super user credentials
        if not self.super_pass and not self.super_key:
            raise ConfigException(
                f"Either super_pass or super_key must be provided for node {self.name}"
            )
        
        # Expand and validate SSH key paths
        if self.owner_key:
            self.owner_key = expand_path(self.owner_key)
            if not os.path.exists(self.owner_key):
                raise ConfigException(
                    f"Owner SSH key not found: {self.owner_key} for node {self.name}"
                )
            # Check key file permissions (should be 600)
            if not check_file_permissions(self.owner_key, 0o600):
                raise ConfigException(
                    f"SSH key {self.owner_key} has incorrect permissions. "
                    f"Should be 600 (rw-------)"
                )
        
        if self.super_key:
            self.super_key = expand_path(self.super_key)
            if not os.path.exists(self.super_key):
                raise ConfigException(
                    f"Super user SSH key not found: {self.super_key} for node {self.name}"
                )
            if not check_file_permissions(self.super_key, 0o600):
                raise ConfigException(
                    f"SSH key {self.super_key} has incorrect permissions. "
                    f"Should be 600 (rw-------)"
                )
        
        # Validate install list
        if not self.install:
            raise ConfigException(
                f"At least one software must be specified for node {self.name}"
            )
    
    def get_software_by_name(self, name: str) -> Optional[SoftwareConfig]:
        """Get software configuration by name."""
        for software in self.install:
            if software.name == name:
                return software
        return None
