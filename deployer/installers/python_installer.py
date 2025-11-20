"""
Python installer implementation.
"""

from typing import Dict, Any
import os

from deployer.installers.base import BaseInstaller
from common.exceptions import InstallException


class PythonInstaller(BaseInstaller):
    """Installer for Python."""
    
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
        Install Python.
        
        Returns:
            Installation results
        """
        self.logger.info(
            f'Installing Python {self.software_config.version}',
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
        """Install Python from system repository."""
        try:
            # Update package list
            self.logger.info('Updating package list', node=self.node_config.name)
            self.run_command('apt-get update -qq', become=True)
            
            # Install Python and essential packages
            self.logger.info('Installing Python', node=self.node_config.name)
            packages = [
                'python3',
                'python3-pip',
                'python3-dev',
                'python3-venv'
            ]
            
            result = self.run_command(
                f'DEBIAN_FRONTEND=noninteractive apt-get install -y {" ".join(packages)}',
                become=True
            )
            
            return {
                'status': 'success',
                'method': 'repository',
                'packages': packages
            }
        except Exception as e:
            raise InstallException(f'Failed to install Python from repository: {e}')
    
    def _install_from_url(self) -> Dict[str, Any]:
        """Install Python from source."""
        if not self.software_config.source_path:
            raise InstallException('source_path is required for URL installation')
        
        try:
            # Install build dependencies
            self.logger.info('Installing build dependencies', node=self.node_config.name)
            build_deps = [
                'build-essential',
                'libssl-dev',
                'zlib1g-dev',
                'libncurses5-dev',
                'libncursesw5-dev',
                'libreadline-dev',
                'libsqlite3-dev',
                'libgdbm-dev',
                'libdb5.3-dev',
                'libbz2-dev',
                'libexpat1-dev',
                'liblzma-dev',
                'tk-dev',
                'libffi-dev'
            ]
            
            self.run_command('apt-get update -qq', become=True)
            self.run_command(
                f'DEBIAN_FRONTEND=noninteractive apt-get install -y {" ".join(build_deps)}',
                become=True
            )
            
            # Download Python source
            self.logger.info(
                f'Downloading Python from {self.software_config.source_path}',
                node=self.node_config.name
            )
            
            tmp_file = f'/tmp/Python-{self.software_config.version}.tgz'
            self.run_command(
                f'wget -q -O {tmp_file} {self.software_config.source_path}',
                become=True
            )
            
            # Extract and build
            self.logger.info('Building Python from source', node=self.node_config.name)
            build_dir = f'/tmp/Python-{self.software_config.version}'
            
            self.run_command(f'tar -xzf {tmp_file} -C /tmp', become=True)
            self.run_command(
                f'cd {build_dir} && ./configure --prefix={self.software_config.install_path} --enable-optimizations',
                become=True
            )
            self.run_command(f'cd {build_dir} && make -j$(nproc)', become=True)
            self.run_command(f'cd {build_dir} && make altinstall', become=True)
            
            # Clean up
            self.run_command(f'rm -rf {tmp_file} {build_dir}', become=True)
            
            return {
                'status': 'success',
                'method': 'source',
                'version': self.software_config.version
            }
        except Exception as e:
            raise InstallException(f'Failed to install Python from source: {e}')
    
    def post_config(self) -> Dict[str, Any]:
        """
        Configure Python environment.
        
        Returns:
            Configuration results
        """
        self.logger.info('Configuring Python environment', node=self.node_config.name)
        
        # Upgrade pip
        try:
            self.run_command('python3 -m pip install --upgrade pip', become=True)
            self.logger.info('Upgraded pip', node=self.node_config.name)
        except Exception as e:
            self.logger.warning(f'Failed to upgrade pip: {e}', node=self.node_config.name)
        
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
