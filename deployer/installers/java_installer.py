"""
Java installer implementation.
"""

from typing import Dict, Any
import os

from deployer.installers.base import BaseInstaller
from common.exceptions import InstallException


class JavaInstaller(BaseInstaller):
    """Installer for Java JDK using Ansible playbook."""
    
    def pre_check(self) -> Dict[str, Any]:
        """
        Check if Java is already installed and verify system requirements.
        
        Returns:
            Dictionary with check results
        """
        self.logger.info(
            f'Running pre-installation checks for Java {self.software_config.version}',
            node=self.node_config.name
        )
        
        checks = {
            'java_installed': False,
            'java_version': None,
            'disk_space_ok': False,
            'install_path_exists': False
        }
        
        # Check if Java is already installed
        try:
            result = self.run_command('java -version 2>&1', become=False)
            if result['rc'] == 0:
                checks['java_installed'] = True
                checks['java_version'] = result['stdout']
                self.logger.info(
                    f'Java is already installed: {result["stdout"][:100]}',
                    node=self.node_config.name
                )
        except Exception:
            self.logger.debug(
                'Java not found on system',
                node=self.node_config.name
            )
        
        # Check disk space (require at least 500MB)
        try:
            result = self.run_command(
                f'df -BM {os.path.dirname(self.software_config.install_path)} | tail -1 | awk \'{{print $4}}\'',
                become=True
            )
            available_mb = int(result['stdout'].strip().replace('M', ''))
            checks['disk_space_ok'] = available_mb >= 500
            self.logger.info(
                f'Available disk space: {available_mb}MB',
                node=self.node_config.name
            )
        except Exception as e:
            self.logger.warning(
                f'Could not check disk space: {e}',
                node=self.node_config.name
            )
        
        # Check if install path exists
        try:
            result = self.run_command(
                f'test -d {self.software_config.install_path} && echo "exists" || echo "not exists"',
                become=True
            )
            checks['install_path_exists'] = 'exists' in result['stdout']
        except Exception:
            pass
        
        return checks
    
    def install(self) -> Dict[str, Any]:
        """
        Install Java JDK using Ansible playbook.
        
        Returns:
            Installation results
        """
        self.logger.info(
            f'Installing Java {self.software_config.version} using Ansible playbook',
            node=self.node_config.name
        )
        
        # Prepare playbook variables
        extra_vars = {
            'java_version': self.software_config.version,
            'java_install_path': self.software_config.install_path,
            'java_source': self.software_config.source,
            'java_source_path': self.software_config.source_path or '',
            'java_set_home': self.software_config.config.get('set_java_home', True),
            'java_add_to_path': self.software_config.config.get('add_to_path', True)
        }
        
        # Get playbook path
        playbook_path = self.get_playbook_path('install_java.yml')
        
        try:
            # Run playbook
            result = self.ansible.run_playbook(
                playbook=playbook_path,
                inventory=self.build_inventory(),
                extra_vars=extra_vars,
                node_name=self.node_config.name,
                check=self.dry_run
            )
            
            if result['rc'] == 0:
                return {
                    'status': 'success',
                    'method': 'playbook',
                    'source': self.software_config.source,
                    'playbook': 'install_java.yml'
                }
            else:
                raise InstallException(
                    f'Playbook execution failed: {result.get("stderr", "Unknown error")}'
                )
                
        except Exception as e:
            raise InstallException(f'Failed to install Java: {e}')
    
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
        Verify Java installation.
        
        Returns:
            Verification results
        """
        self.logger.info('Verifying Java installation', node=self.node_config.name)
        
        try:
            # Check Java version
            result = self.run_command('java -version 2>&1', become=False)
            
            if result['rc'] == 0:
                self.logger.info(
                    f'Java verification successful: {result["stdout"][:100]}',
                    node=self.node_config.name
                )
                return {
                    'status': 'success',
                    'verified': True,
                    'version_output': result['stdout']
                }
            else:
                raise InstallException('Java command not found after installation')
                
        except Exception as e:
            raise InstallException(f'Java verification failed: {e}')
