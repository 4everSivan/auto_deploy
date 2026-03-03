"""
Ansible wrapper for executing playbooks and ad-hoc commands.
"""

import os
import tempfile
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

import ansible_runner  # type: ignore[import-untyped]

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
        self.cancel_callback: Optional[Callable[[], bool]] = None
    
    def run_playbook(
        self,
        playbook: str,
        inventory: Dict[str, Any],
        extra_vars: Optional[Dict[str, Any]] = None,
        node_name: Optional[str] = None,
        check: bool = False,
        cancel_callback: Optional[Callable[[], bool]] = None
    ) -> Dict[str, Any]:
        """
        Run an Ansible playbook.
        
        Args:
            playbook: Path to playbook file
            inventory: Ansible inventory dictionary
            extra_vars: Extra variables to pass to playbook
            node_name: Node name for logging
            check: Whether to run in check mode (dry run)
            cancel_callback: Optional callback to cancel execution
            
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
                # Prepare runner arguments
                runner_args = {
                    'private_data_dir': tmpdir,
                    'playbook': playbook,
                    'inventory': inventory_path,
                    'extravars': extra_vars or {},
                    'envvars': {
                        'ANSIBLE_HOST_KEY_CHECKING': 'False',
                        'ANSIBLE_SSH_ARGS': '-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no',
                        'LC_ALL': 'en_US.UTF-8',
                        'LANG': 'en_US.UTF-8',
                        'LC_CTYPE': 'en_US.UTF-8'
                    },
                    'quiet': True,
                    'verbosity': 1,
                    'cancel_callback': cancel_callback or self.cancel_callback
                }
                
                if check:
                    runner_args['cmdline'] = '--check'
                
                # Run playbook
                result = ansible_runner.run(**runner_args)
                
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
                    
                    # Get failure details
                    failures = []
                    # In some versions of ansible-runner, events is a generator, so we convert to list
                    event_list = list(result.events)
                    if event_list:
                        for event in event_list:
                            event_type = event.get('event')
                            if event_type in ['runner_on_failed', 'runner_on_unreachable', 'runner_on_error', 'runner_on_skipped']:
                                event_data = event.get('event_data', {})
                                res = event_data.get('res', {})
                                msg = res.get('msg', res.get('stderr', res.get('stdout', 'Unknown error')))
                                failures.append(f"[{event_type}] {msg}")
                    
                    if not failures:
                        # Try to get something from stdout if no events matched
                        stdout_content = result.stdout.read() if hasattr(result.stdout, 'read') else str(result.stdout)
                        if stdout_content:
                            # Get last 5 lines of stdout
                            last_lines = '\n'.join(stdout_content.strip().split('\n')[-5:])
                            failures.append(f"Stdout summary: {last_lines}")

                    if failures:
                        error_msg = f"{error_msg}. Details: {'; '.join(failures)}"
                    else:
                        error_msg = f"{error_msg}. (No specific failure details found)"
                        
                    self.logger.error(error_msg, node=node_name)
                    raise AnsibleException(error_msg)
                    
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
        become_user: Optional[str] = None,
        become_password: Optional[str] = None,
        node_name: Optional[str] = None,
        check: bool = False,
        cancel_callback: Optional[Callable[[], bool]] = None
    ) -> Dict[str, Any]:
        """
        Run an ad-hoc shell command.
        
        Args:
            host: Target host
            command: Shell command to run
            user: SSH user
            password: SSH password
            ssh_key: Path to SSH private key
            port: SSH port
            become: Whether to use sudo
            become_user: User to become
            become_password: Sudo password
            node_name: Node name for logging
            check: Whether to run in check mode (dry run)
            cancel_callback: Optional callback to cancel execution
            
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
            
            # Prepare runner arguments
            runner_args = {
                'private_data_dir': tmpdir,
                'host_pattern': host,
                'module': 'shell',
                'module_args': command,
                'inventory': inventory_path,
                'envvars': {
                    'ANSIBLE_HOST_KEY_CHECKING': 'False',
                    'ANSIBLE_SSH_ARGS': '-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no',
                    'LC_ALL': 'en_US.UTF-8',
                    'LANG': 'en_US.UTF-8',
                    'LC_CTYPE': 'en_US.UTF-8'
                },
                'quiet': True,
                'cancel_callback': cancel_callback or self.cancel_callback
            }
            
            if check:
                runner_args['cmdline'] = '--check'
            
            try:
                result = ansible_runner.run(**runner_args)
                
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
                    error_msg = f'Command failed with status: {result.status}'
                    
                    # Get failure details
                    failure_details = []
                    event_list = list(result.events)
                    if event_list:
                        for event in event_list:
                            event_type = event.get('event')
                            if event_type in ['runner_on_unreachable', 'runner_on_failed', 'runner_on_error']:
                                event_data = event.get('event_data', {})
                                res = event_data.get('res', {})
                                msg = res.get('msg', res.get('stderr', res.get('stdout', 'Command execution failed')))
                                failure_details.append(f"[{event_type}] {msg}")
                    
                    if not failure_details:
                        stdout_content = result.stdout.read() if hasattr(result.stdout, 'read') else str(result.stdout)
                        if stdout_content:
                            last_lines = '\n'.join(stdout_content.strip().split('\n')[-5:])
                            failure_details.append(f"Stdout summary: {last_lines}")

                    if failure_details:
                        error_msg = f"{error_msg}. Details: {'; '.join(failure_details)}"
                    else:
                        error_msg = f"{error_msg}. (No specific failure details found)"
                        
                    raise AnsibleException(error_msg)
                    
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
