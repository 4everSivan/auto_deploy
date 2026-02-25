"""
Configuration models for node and software configurations using Pydantic.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
import os

from common.utils import expand_path, validate_port, check_file_permissions
from common.exceptions import ConfigException


class SoftwareConfig(BaseModel):
    """Software installation configuration."""
    
    name: str
    version: str
    install_path: str
    source: str = 'repository'  # local/url/repository
    source_path: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("Software name is required")
        return v

    @field_validator('version')
    @classmethod
    def version_must_not_be_empty(cls, v: str, info: ValidationInfo) -> str:
        if not v:
            raise ValueError(f"Version is required for {info.data.get('name', 'software')}")
        return v

    @field_validator('install_path')
    @classmethod
    def validate_install_path(cls, v: str) -> str:
        if not v:
            raise ValueError("Install path is required")
        return expand_path(v)

    @model_validator(mode='after')
    def validate_source_and_path(self) -> 'SoftwareConfig':
        if self.source not in ['local', 'url', 'repository']:
            raise ValueError(
                f"Invalid source '{self.source}' for {self.name}. "
                f"Must be one of: local, url, repository"
            )
        
        if self.source in ['local', 'url'] and not self.source_path:
            raise ValueError(
                f"source_path is required when source is '{self.source}' for {self.name}"
            )
        
        if self.source == 'local' and self.source_path:
            expanded = expand_path(self.source_path)
            if not os.path.exists(expanded):
                raise ValueError(
                    f"Source file not found: {expanded} for {self.name}"
                )
            # We don't necessarily update the attribute here if we want to keep raw value, 
            # but usually it's better to store expanded path.
            # However, pydantic models are immutable-ish by default if configured, 
            # but following previous logic:
            self.source_path = expanded
            
        return self


class NodeConfig(BaseModel):
    """Node connection and deployment configuration."""
    
    name: str
    host: str
    port: int = 22
    owner_user: str
    owner_pass: Optional[str] = None
    owner_key: Optional[str] = None
    super_user: str = 'root'
    super_pass: Optional[str] = None
    super_key: Optional[str] = None
    install: List[SoftwareConfig] = Field(default_factory=list)
    
    @field_validator('port')
    @classmethod
    def validate_node_port(cls, v: int) -> int:
        if not validate_port(v):
            raise ValueError(
                f"Invalid port {v}. Port must be between 1 and 65535"
            )
        return v

    @model_validator(mode='after')
    def validate_node_config(self) -> 'NodeConfig':
        if not self.name:
            raise ValueError("Node name is required")
        if not self.host:
            raise ValueError(f"Host is required for node {self.name}")
        if not self.owner_user:
            raise ValueError(f"owner_user is required for node {self.name}")
        
        if not self.owner_pass and not self.owner_key:
            raise ValueError(
                f"Either owner_pass or owner_key must be provided for node {self.name}"
            )
        
        if not self.super_pass and not self.super_key:
            raise ValueError(
                f"Either super_pass or super_key must be provided for node {self.name}"
            )
        
        # Validate SSH keys
        if self.owner_key:
            self.owner_key = expand_path(self.owner_key)
            if not os.path.exists(self.owner_key):
                raise ValueError(
                    f"Owner SSH key not found: {self.owner_key} for node {self.name}"
                )
            if not check_file_permissions(self.owner_key, 0o600):
                raise ValueError(
                    f"SSH key {self.owner_key} has incorrect permissions. "
                    f"Should be 600"
                )
        
        if self.super_key:
            self.super_key = expand_path(self.super_key)
            if not os.path.exists(self.super_key):
                raise ValueError(
                    f"Super user SSH key not found: {self.super_key} for node {self.name}"
                )
            if not check_file_permissions(self.super_key, 0o600):
                raise ValueError(
                    f"SSH key {self.super_key} has incorrect permissions. "
                    f"Should be 600"
                )
        
        if not self.install:
            raise ValueError(
                f"At least one software must be specified for node {self.name}"
            )
            
        return self

    def get_software_by_name(self, name: str) -> Optional[SoftwareConfig]:
        """Get software configuration by name."""
        for software in self.install:
            if software.name == name:
                return software
        return None
