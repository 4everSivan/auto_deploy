"""
Zookeeper installer implementation.
"""

from typing import Dict, Any
import os

from deployer.installers.base import BaseInstaller
from common.exceptions import InstallException


class ZookeeperInstaller(BaseInstaller):
    """Installer for Apache Zookeeper."""
    
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
        Install Zookeeper.
        
        Returns:
            Installation results
        """
        self.logger.info(
            f'Installing Zookeeper {self.software_config.version}',
            node=self.node_config.name
        )
        
        # Create installation directory
        try:
            self.run_command(
                f'mkdir -p {self.software_config.install_path}',
                become=True
            )
        except Exception as e:
            raise InstallException(f'Failed to create install directory: {e}')
        
        # Install based on source type
        if self.software_config.source == 'repository':
            return self._install_from_repository()
        elif self.software_config.source == 'url':
            return self._install_from_url()
        else:
            raise InstallException(f'Unsupported source: {self.software_config.source}')
    
    def _install_from_repository(self) -> Dict[str, Any]:
        """Install Zookeeper from system repository."""
        try:
            # Update package list
            self.logger.info('Updating package list', node=self.node_config.name)
            self.run_command('apt-get update -qq', become=True)
            
            # Install Zookeeper
            self.logger.info('Installing Zookeeper', node=self.node_config.name)
            result = self.run_command(
                'DEBIAN_FRONTEND=noninteractive apt-get install -y zookeeper zookeeperd',
                become=True
            )
            
            return {
                'status': 'success',
                'method': 'repository'
            }
        except Exception as e:
            raise InstallException(f'Failed to install Zookeeper from repository: {e}')
    
    def _install_from_url(self) -> Dict[str, Any]:
        """Install Zookeeper from URL."""
        if not self.software_config.source_path:
            # Use default Apache mirror
            version = self.software_config.version
            self.software_config.source_path = (
                f'https://archive.apache.org/dist/zookeeper/'
                f'zookeeper-{version}/apache-zookeeper-{version}-bin.tar.gz'
            )
        
        try:
            # Download Zookeeper archive
            self.logger.info(
                f'Downloading Zookeeper from {self.software_config.source_path}',
                node=self.node_config.name
            )
            
            tmp_file = f'/tmp/zookeeper-{self.software_config.version}.tar.gz'
            self.run_command(
                f'wget -q -O {tmp_file} {self.software_config.source_path}',
                become=True
            )
            
            # Extract archive
            self.logger.info('Extracting Zookeeper archive', node=self.node_config.name)
            self.run_command(
                f'tar -xzf {tmp_file} -C {self.software_config.install_path} --strip-components=1',
                become=True
            )
            
            # Clean up
            self.run_command(f'rm -f {tmp_file}', become=True)
            
            return {
                'status': 'success',
                'method': 'url',
                'source': self.software_config.source_path
            }
        except Exception as e:
            raise InstallException(f'Failed to install Zookeeper from URL: {e}')
    
    def post_config(self) -> Dict[str, Any]:
        """
        Configure Zookeeper.
        
        Returns:
            Configuration results
        """
        self.logger.info('Configuring Zookeeper', node=self.node_config.name)
        
        config = self.software_config.config
        
        # Create data directory
        data_dir = config.get('data_dir', '/var/lib/zookeeper')
        try:
            self.run_command(f'mkdir -p {data_dir}', become=True)
            self.logger.info(f'Created data directory: {data_dir}', node=self.node_config.name)
        except Exception as e:
            self.logger.warning(f'Failed to create data directory: {e}', node=self.node_config.name)
        
        # Create zoo.cfg configuration file
        client_port = config.get('client_port', 2181)
        tick_time = config.get('tick_time', 2000)
        init_limit = config.get('init_limit', 10)
        sync_limit = config.get('sync_limit', 5)
        
        zoo_cfg = f"""# Zookeeper configuration
tickTime={tick_time}
initLimit={init_limit}
syncLimit={sync_limit}
dataDir={data_dir}
clientPort={client_port}
"""
        
        try:
            # Write configuration
            conf_dir = f'{self.software_config.install_path}/conf'
            self.run_command(f'mkdir -p {conf_dir}', become=True)
            self.run_command(
                f'cat > {conf_dir}/zoo.cfg << EOF\n{zoo_cfg}\nEOF',
                become=True
            )
            self.logger.info('Created zoo.cfg configuration', node=self.node_config.name)
        except Exception as e:
            self.logger.warning(f'Failed to create zoo.cfg: {e}', node=self.node_config.name)
        
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
