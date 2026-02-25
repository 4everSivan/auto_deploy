"""
Ansible wrapper for executing playbooks and ad-hoc commands.
"""

import os
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path

import ansible_runner

from common.exceptions import AnsibleException, ConnectionException
from common.logger import DeployLogger


class AnsibleWrapper:
    """Wrapper for ansible_runner to execute playbooks and commands."""
    
    def __init__(self, logger: DeployLogger):
        """
        Initialize Ansible wrapper.
        
        Args:
            logger: Logger instance for logging
        """
        self.logger = logger
    
    def run_playbook(
        self,
        playbook: str,
        inventory: Dict[str, Any],
        extra_vars: Optional[Dict[str, Any]] = None,
        node_name: Optional[str] = None,
        check: bool = False
    ) -> Dict[str, Any]:
        """
        Run an Ansible playbook.
        
        Args:
            playbook: Path to playbook file
            inventory: Ansible inventory dictionary
            extra_vars: Extra variables to pass to playbook
            node_name: Node name for logging
            check: Whether to run in check mode (dry run)
            
        Returns:
            Dictionary with execution results
            
        Raises:
            AnsibleException: If playbook execution fails
        """
        if not os.path.exists(playbook):
            raise AnsibleException(f'Playbook not found: {playbook}')
        
        # Create temporary directory for ansible-runner
        with tempfile.TemporaryDirectory() as tmpdir:
            # Prepare inventory
            inventory_path = os.path.join(tmpdir, 'inventory')
            self._write_inventory(inventory_path, inventory)
            
            # Log execution start
            self.logger.info(
                f'Running playbook: {os.path.basename(playbook)}',
                node=node_name
            )
            
            try:
                # Run playbook
                result = ansible_runner.run(
                    private_data_dir=tmpdir,
                    playbook=playbook,
                    inventory=inventory_path,
                    extravars=extra_vars or {},
                    quiet=False,
                    verbosity=1,
                    check=check
                )
                
                # Check result
                if result.status == 'successful':
                    self.logger.info(
                        f'Playbook completed successfully',
                        node=node_name
                    )
                    return {
                        'status': 'success',
                        'rc': result.rc,
                        'stats': result.stats
                    }
                else:
                    error_msg = f'Playbook failed with status: {result.status}'
                    self.logger.error(error_msg, node=node_name)
                    
                    # Get failure details
                    failures = []
                    if result.events:
                        for event in result.events:
                            if event.get('event') == 'runner_on_failed':
                                failures.append(event.get('event_data', {}))
                    
                    raise AnsibleException(
                        f'{error_msg}. RC: {result.rc}. Failures: {failures}'
                    )
                    
            except Exception as e:
                if isinstance(e, AnsibleException):
                    raise
                self.logger.exception(
                    f'Error running playbook: {e}',
                    node=node_name
                )
                raise AnsibleException(f'Playbook execution error: {e}')
    
    def run_command(
        self,
        host: str,
        command: str,
        user: str,
        password: Optional[str] = None,
        ssh_key: Optional[str] = None,
        port: int = 22,
        become: bool = False,
        become_user: str = 'root',
        become_password: Optional[str] = None,
        node_name: Optional[str] = None,
        check: bool = False
    ) -> Dict[str, Any]:
        """
        Run an ad-hoc command on a remote host.
        
        Args:
            host: Target host
            command: Command to execute
            user: SSH user
            password: SSH password
            ssh_key: Path to SSH private key
            port: SSH port
            become: Whether to use privilege escalation
            become_user: User to become
            become_password: Password for privilege escalation
            node_name: Node name for logging
            check: Whether to run in check mode (dry run)
            
        Returns:
            Dictionary with command results
            
        Raises:
            AnsibleException: If command execution fails
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Prepare inventory
            inventory = {
                'all': {
                    'hosts': {
                        host: {
                            'ansible_host': host,
                            'ansible_port': port,
                            'ansible_user': user
                        }
                    }
                }
            }
            
            # Add authentication
            if ssh_key:
                inventory['all']['hosts'][host]['ansible_ssh_private_key_file'] = ssh_key
            elif password:
                inventory['all']['hosts'][host]['ansible_password'] = password
            else:
                raise AnsibleException('Either password or ssh_key must be provided')
            
            # Add become settings
            if become:
                inventory['all']['hosts'][host]['ansible_become'] = True
                inventory['all']['hosts'][host]['ansible_become_user'] = become_user
                if become_password:
                    inventory['all']['hosts'][host]['ansible_become_password'] = become_password
            
            inventory_path = os.path.join(tmpdir, 'inventory')
            self._write_inventory(inventory_path, inventory)
            
            self.logger.debug(
                f'Running command on {host}: {command}',
                node=node_name
            )
            
            try:
                result = ansible_runner.run(
                    private_data_dir=tmpdir,
                    host_pattern=host,
                    module='shell',
                    module_args=command,
                    inventory=inventory_path,
                    quiet=True,
                    check=check
                )
                
                if result.status == 'successful':
                    # Get command output
                    output = ''
                    rc = 0
                    for event in result.events:
                        if event.get('event') == 'runner_on_ok':
                            event_data = event.get('event_data', {})
                            res = event_data.get('res', {})
                            output = res.get('stdout', '')
                            rc = res.get('rc', 0)
                    
                    return {
                        'status': 'success',
                        'rc': rc,
                        'stdout': output,
                        'stderr': ''
                    }
                else:
                    raise AnsibleException(
                        f'Command failed with status: {result.status}'
                    )
                    
            except Exception as e:
                if isinstance(e, AnsibleException):
                    raise
                self.logger.exception(
                    f'Error running command: {e}',
                    node=node_name
                )
                raise AnsibleException(f'Command execution error: {e}')
    
    def test_connection(
        self,
        host: str,
        user: str,
        password: Optional[str] = None,
        ssh_key: Optional[str] = None,
        port: int = 22,
        node_name: Optional[str] = None
    ) -> bool:
        """
        Test SSH connection to a host.
        
        Args:
            host: Target host
            user: SSH user
            password: SSH password
            ssh_key: Path to SSH private key
            port: SSH port
            node_name: Node name for logging
            
        Returns:
            True if connection successful
            
        Raises:
            ConnectionException: If connection fails
        """
        try:
            result = self.run_command(
                host=host,
                command='echo "Connection test"',
                user=user,
                password=password,
                ssh_key=ssh_key,
                port=port,
                node_name=node_name
            )
            
            if result['status'] == 'success':
                self.logger.info(
                    f'SSH connection to {host}:{port} successful',
                    node=node_name
                )
                return True
            else:
                raise ConnectionException(
                    f'Connection test failed for {host}:{port}'
                )
                
        except Exception as e:
            self.logger.error(
                f'SSH connection to {host}:{port} failed: {e}',
                node=node_name
            )
            raise ConnectionException(
                f'Failed to connect to {host}:{port}: {e}'
            )
    
    def _write_inventory(self, path: str, inventory: Dict[str, Any]) -> None:
        """
        Write inventory dictionary to YAML file.
        
        Args:
            path: Path to write inventory file
            inventory: Inventory dictionary
        """
        import yaml
        
        with open(path, 'w') as f:
            yaml.dump(inventory, f, default_flow_style=False)
