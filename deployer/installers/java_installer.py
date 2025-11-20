"""
Java installer implementation.
"""

from typing import Dict, Any
import os

from deployer.installers.base import BaseInstaller
from common.exceptions import InstallException


class JavaInstaller(BaseInstaller):
    """Installer for Java JDK."""
    
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
        Install Java JDK.
        
        Returns:
            Installation results
        """
        self.logger.info(
            f'Installing Java {self.software_config.version}',
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
        elif self.software_config.source == 'local':
            return self._install_from_local()
        else:
            raise InstallException(f'Unsupported source: {self.software_config.source}')
    
    def _install_from_repository(self) -> Dict[str, Any]:
        """Install Java from system repository."""
        version_map = {
            '8': 'openjdk-8-jdk',
            '11': 'openjdk-11-jdk',
            '17': 'openjdk-17-jdk'
        }
        
        package = version_map.get(self.software_config.version, 'default-jdk')
        
        try:
            # Update package list
            self.logger.info('Updating package list', node=self.node_config.name)
            self.run_command('apt-get update -qq', become=True)
            
            # Install Java
            self.logger.info(f'Installing {package}', node=self.node_config.name)
            result = self.run_command(
                f'DEBIAN_FRONTEND=noninteractive apt-get install -y {package}',
                become=True
            )
            
            return {
                'status': 'success',
                'method': 'repository',
                'package': package
            }
        except Exception as e:
            raise InstallException(f'Failed to install Java from repository: {e}')
    
    def _install_from_url(self) -> Dict[str, Any]:
        """Install Java from URL."""
        if not self.software_config.source_path:
            raise InstallException('source_path is required for URL installation')
        
        try:
            # Download Java archive
            self.logger.info(
                f'Downloading Java from {self.software_config.source_path}',
                node=self.node_config.name
            )
            
            tmp_file = f'/tmp/jdk-{self.software_config.version}.tar.gz'
            self.run_command(
                f'wget -q -O {tmp_file} {self.software_config.source_path}',
                become=True
            )
            
            # Extract archive
            self.logger.info('Extracting Java archive', node=self.node_config.name)
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
            raise InstallException(f'Failed to install Java from URL: {e}')
    
    def _install_from_local(self) -> Dict[str, Any]:
        """Install Java from local file."""
        raise InstallException('Local installation not yet implemented')
    
    def post_config(self) -> Dict[str, Any]:
        """
        Configure Java environment variables.
        
        Returns:
            Configuration results
        """
        self.logger.info('Configuring Java environment', node=self.node_config.name)
        
        config = self.software_config.config
        
        if config.get('set_java_home', False):
            # Set JAVA_HOME
            java_home = self.software_config.install_path
            
            # Add to /etc/environment
            try:
                self.run_command(
                    f'echo "JAVA_HOME={java_home}" >> /etc/environment',
                    become=True
                )
                self.logger.info(f'Set JAVA_HOME={java_home}', node=self.node_config.name)
            except Exception as e:
                self.logger.warning(f'Failed to set JAVA_HOME: {e}', node=self.node_config.name)
        
        if config.get('add_to_path', False):
            # Add Java bin to PATH
            try:
                self.run_command(
                    f'echo "export PATH={self.software_config.install_path}/bin:$PATH" >> /etc/profile.d/java.sh',
                    become=True
                )
                self.logger.info('Added Java to PATH', node=self.node_config.name)
            except Exception as e:
                self.logger.warning(f'Failed to add Java to PATH: {e}', node=self.node_config.name)
        
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
