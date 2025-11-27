"""
Zookeeper installer implementation.
"""

from typing import Dict, Any
import os

from deployer.installers.base import BaseInstaller
from common.exceptions import InstallException


class ZookeeperInstaller(BaseInstaller):
    """Installer for Apache Zookeeper using Ansible playbook."""
    
    def pre_check(self) -> Dict[str, Any]:
        """
        Check if Zookeeper is already installed and verify system requirements.
        
        Returns:
            Dictionary with check results
        """
        self.logger.info(
            f'Running pre-installation checks for Zookeeper {self.software_config.version}',
            node=self.node_config.name
        )
        
        checks = {
            'zookeeper_installed': False,
            'java_installed': False,
            'disk_space_ok': False
        }
        
        # Check if Zookeeper is already installed
        try:
            result = self.run_command(
                f'test -f {self.software_config.install_path}/bin/zkServer.sh && echo "installed"',
                become=True
            )
            checks['zookeeper_installed'] = 'installed' in result['stdout']
            if checks['zookeeper_installed']:
                self.logger.info('Zookeeper is already installed', node=self.node_config.name)
        except Exception:
            pass
        
        # Check if Java is installed (required for Zookeeper)
        try:
            result = self.run_command('java -version 2>&1', become=False)
            checks['java_installed'] = result['rc'] == 0
            if checks['java_installed']:
                self.logger.info('Java is installed', node=self.node_config.name)
            else:
                self.logger.warning('Java is not installed (required for Zookeeper)', node=self.node_config.name)
        except Exception:
            self.logger.warning('Java is not installed (required for Zookeeper)', node=self.node_config.name)
        
        # Check disk space (require at least 200MB)
        try:
            result = self.run_command(
                f'df -BM {os.path.dirname(self.software_config.install_path)} | tail -1 | awk \'{{print $4}}\'',
                become=True
            )
            available_mb = int(result['stdout'].strip().replace('M', ''))
            checks['disk_space_ok'] = available_mb >= 200
            self.logger.info(f'Available disk space: {available_mb}MB', node=self.node_config.name)
        except Exception as e:
            self.logger.warning(f'Could not check disk space: {e}', node=self.node_config.name)
        
        return checks
    
    def install(self) -> Dict[str, Any]:
        """
        Install Zookeeper using Ansible playbook.
        
        Returns:
            Installation results
        """
        self.logger.info(
            f'Installing Zookeeper {self.software_config.version} using Ansible playbook',
            node=self.node_config.name
        )
        
        # Prepare playbook variables
        extra_vars = {
            'zk_version': self.software_config.version,
            'zk_install_path': self.software_config.install_path,
            'zk_source': self.software_config.source,
            'zk_source_path': self.software_config.source_path or '',
            'zk_data_dir': self.software_config.config.get('data_dir', '/var/lib/zookeeper'),
            'zk_client_port': self.software_config.config.get('client_port', 2181),
            'zk_tick_time': self.software_config.config.get('tick_time', 2000),
            'zk_init_limit': self.software_config.config.get('init_limit', 10),
            'zk_sync_limit': self.software_config.config.get('sync_limit', 5)
        }
        
        # Get playbook path
        playbook_path = self.get_playbook_path('install_zookeeper.yml')
        
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
                    'playbook': 'install_zookeeper.yml'
                }
            else:
                raise InstallException(
                    f'Playbook execution failed: {result.get("stderr", "Unknown error")}'
                )
                
        except Exception as e:
            raise InstallException(f'Failed to install Zookeeper: {e}')
    
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
        Verify Zookeeper installation.
        
        Returns:
            Verification results
        """
        self.logger.info('Verifying Zookeeper installation', node=self.node_config.name)
        
        try:
            # Check if zkServer.sh exists
            result = self.run_command(
                f'test -f {self.software_config.install_path}/bin/zkServer.sh && echo "found"',
                become=True
            )
            
            if 'found' in result['stdout']:
                self.logger.info(
                    'Zookeeper verification successful',
                    node=self.node_config.name
                )
                
                # Try to get version
                try:
                    version_result = self.run_command(
                        f'{self.software_config.install_path}/bin/zkServer.sh version',
                        become=True
                    )
                    version_info = version_result['stdout']
                except Exception:
                    version_info = 'Version info not available'
                
                return {
                    'status': 'success',
                    'verified': True,
                    'version_info': version_info
                }
            else:
                raise InstallException('Zookeeper binaries not found after installation')
                
        except Exception as e:
            raise InstallException(f'Zookeeper verification failed: {e}')
