"""
Base installer class for software installation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

from deployer.models import NodeConfig, SoftwareConfig
from deployer.ansible_wrapper import AnsibleWrapper
from common.logger import DeployLogger
from common.exceptions import InstallException


class BaseInstaller(ABC):
    """Abstract base class for software installers."""
    
    def __init__(
        self,
        node_config: NodeConfig,
        software_config: SoftwareConfig,
        ansible_wrapper: AnsibleWrapper,
        logger: DeployLogger
    ):
        """
        Initialize installer.
        
        Args:
            node_config: Node configuration
            software_config: Software configuration
            ansible_wrapper: Ansible wrapper instance
            logger: Logger instance
        """
        self.node_config = node_config
        self.software_config = software_config
        self.ansible = ansible_wrapper
        self.logger = logger
    
    @abstractmethod
    def pre_check(self) -> Dict[str, Any]:
        """
        Perform pre-installation checks.
        
        Returns:
            Dictionary with check results
            
        Raises:
            InstallException: If critical checks fail
        """
        pass
    
    @abstractmethod
    def install(self) -> Dict[str, Any]:
        """
        Install the software.
        
        Returns:
            Dictionary with installation results
            
        Raises:
            InstallException: If installation fails
        """
        pass
    
    @abstractmethod
    def post_config(self) -> Dict[str, Any]:
        """
        Perform post-installation configuration.
        
        Returns:
            Dictionary with configuration results
            
        Raises:
            InstallException: If configuration fails
        """
        pass
    
    @abstractmethod
    def verify(self) -> Dict[str, Any]:
        """
        Verify installation.
        
        Returns:
            Dictionary with verification results
            
        Raises:
            InstallException: If verification fails
        """
        pass
    
    def get_playbook_path(self, playbook_name: str) -> str:
        """
        Get path to playbook file.
        
        Args:
            playbook_name: Name of playbook file
            
        Returns:
            Absolute path to playbook
            
        Raises:
            InstallException: If playbook not found
        """
        # Get project root directory
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        playbook_path = project_root / 'playbook' / playbook_name
        
        if not playbook_path.exists():
            raise InstallException(
                f'Playbook not found: {playbook_path}'
            )
        
        return str(playbook_path)
    
    def build_inventory(self) -> Dict[str, Any]:
        """
        Build Ansible inventory for the node.
        
        Returns:
            Ansible inventory dictionary
        """
        host_vars = {
            'ansible_host': self.node_config.host,
            'ansible_port': self.node_config.port,
            'ansible_user': self.node_config.owner_user
        }
        
        # Add authentication
        if self.node_config.owner_key:
            host_vars['ansible_ssh_private_key_file'] = self.node_config.owner_key
        elif self.node_config.owner_pass:
            host_vars['ansible_password'] = self.node_config.owner_pass
        
        # Add become settings
        host_vars['ansible_become'] = True
        host_vars['ansible_become_user'] = self.node_config.super_user
        
        if self.node_config.super_key:
            host_vars['ansible_become_ssh_private_key_file'] = self.node_config.super_key
        elif self.node_config.super_pass:
            host_vars['ansible_become_password'] = self.node_config.super_pass
        
        inventory = {
            'all': {
                'hosts': {
                    self.node_config.name: host_vars
                }
            }
        }
        
        return inventory
    
    def run_command(
        self,
        command: str,
        become: bool = False
    ) -> Dict[str, Any]:
        """
        Run a command on the node.
        
        Args:
            command: Command to execute
            become: Whether to use privilege escalation
            
        Returns:
            Command execution results
        """
        return self.ansible.run_command(
            host=self.node_config.host,
            command=command,
            user=self.node_config.owner_user,
            password=self.node_config.owner_pass,
            ssh_key=self.node_config.owner_key,
            port=self.node_config.port,
            become=become,
            become_user=self.node_config.super_user,
            become_password=self.node_config.super_pass,
            node_name=self.node_config.name
        )
