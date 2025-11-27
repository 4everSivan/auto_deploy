"""
Python installer implementation.
"""

from typing import Dict, Any
import os

from deployer.installers.base import BaseInstaller
from common.exceptions import InstallException


class PythonInstaller(BaseInstaller):
    """Installer for Python using Ansible playbook."""
    
    def pre_check(self) -> Dict[str, Any]:
        """
        Check if Python is already installed and verify system requirements.
        
        Returns:
            Dictionary with check results
        """
        self.logger.info(
            f'Running pre-installation checks for Python {self.software_config.version}',
            node=self.node_config.name
        )
        
        checks = {
            'python_installed': False,
            'python_version': None,
            'disk_space_ok': False
        }
        
        # Check if Python is already installed
        try:
            result = self.run_command('python3 --version', become=False)
            if result['rc'] == 0:
                checks['python_installed'] = True
                checks['python_version'] = result['stdout'].strip()
                self.logger.info(
                    f'Python is already installed: {checks["python_version"]}',
                    node=self.node_config.name
                )
        except Exception:
            self.logger.debug('Python not found on system', node=self.node_config.name)
        
        # Check disk space (require at least 300MB)
        try:
            result = self.run_command(
                f'df -BM {os.path.dirname(self.software_config.install_path)} | tail -1 | awk \'{{print $4}}\'',
                become=True
            )
            available_mb = int(result['stdout'].strip().replace('M', ''))
            checks['disk_space_ok'] = available_mb >= 300
            self.logger.info(
                f'Available disk space: {available_mb}MB',
                node=self.node_config.name
            )
        except Exception as e:
            self.logger.warning(f'Could not check disk space: {e}', node=self.node_config.name)
        
        return checks
    
    def install(self) -> Dict[str, Any]:
        """
        Install Python using Ansible playbook.
        
        Returns:
            Installation results
        """
        self.logger.info(
            f'Installing Python {self.software_config.version} using Ansible playbook',
            node=self.node_config.name
        )
        
        # Prepare playbook variables
        extra_vars = {
            'python_version': self.software_config.version,
            'python_install_path': self.software_config.install_path,
            'python_source': self.software_config.source,
            'python_source_path': self.software_config.source_path or '',
            'python_install_pip': True,
            'python_install_venv': True
        }
        
        # Get playbook path
        playbook_path = self.get_playbook_path('install_python.yml')
        
        try:
            # Run playbook
            result = self.ansible.run_playbook(
                playbook=playbook_path,
                inventory=self.build_inventory(),
                extra_vars=extra_vars,
                node_name=self.node_config.name
            )
            
            if result['rc'] == 0:
                return {
                    'status': 'success',
                    'method': 'playbook',
                    'source': self.software_config.source,
                    'playbook': 'install_python.yml'
                }
            else:
                raise InstallException(
                    f'Playbook execution failed: {result.get("stderr", "Unknown error")}'
                )
                
        except Exception as e:
            raise InstallException(f'Failed to install Python: {e}')
    
    def post_config(self) -> Dict[str, Any]:
        """
        Post-configuration is handled by the playbook.
        
        Returns:
            Configuration results
        """
        self.logger.info(
            'Post-configuration handled by playbook',
            node=self.node_config.name
        )
        
        return {'status': 'success', 'configured': True}
    
    def verify(self) -> Dict[str, Any]:
        """
        Verify Python installation.
        
        Returns:
            Verification results
        """
        self.logger.info('Verifying Python installation', node=self.node_config.name)
        
        try:
            # Check Python version
            result = self.run_command('python3 --version', become=False)
            
            if result['rc'] == 0:
                version = result['stdout'].strip()
                self.logger.info(
                    f'Python verification successful: {version}',
                    node=self.node_config.name
                )
                
                # Check pip
                pip_result = self.run_command('python3 -m pip --version', become=False)
                
                return {
                    'status': 'success',
                    'verified': True,
                    'python_version': version,
                    'pip_version': pip_result['stdout'].strip() if pip_result['rc'] == 0 else None
                }
            else:
                raise InstallException('Python command not found after installation')
                
        except Exception as e:
            raise InstallException(f'Python verification failed: {e}')
