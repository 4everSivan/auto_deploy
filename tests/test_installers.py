"""
Tests for deployer.installers module.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import os

from deployer.installers import get_installer, INSTALLER_REGISTRY
from deployer.installers.base import BaseInstaller
from deployer.installers.java_installer import JavaInstaller
from deployer.installers.python_installer import PythonInstaller
from deployer.installers.zookeeper_installer import ZookeeperInstaller
from deployer.models import NodeConfig, SoftwareConfig
from deployer.ansible_wrapper import AnsibleWrapper
from common.logger import DeployLogger
from common.exceptions import InstallException


class TestInstallerRegistry:
    """Tests for installer registry."""
    
    def test_registry_contains_all_installers(self):
        """Test that registry contains all expected installers."""
        assert 'java' in INSTALLER_REGISTRY
        assert 'python' in INSTALLER_REGISTRY
        assert 'zookeeper' in INSTALLER_REGISTRY
    
    def test_get_installer_java(self):
        """Test getting Java installer."""
        installer_class = get_installer('java')
        assert installer_class == JavaInstaller
    
    def test_get_installer_python(self):
        """Test getting Python installer."""
        installer_class = get_installer('python')
        assert installer_class == PythonInstaller
    
    def test_get_installer_zookeeper(self):
        """Test getting Zookeeper installer."""
        installer_class = get_installer('zookeeper')
        assert installer_class == ZookeeperInstaller
    
    def test_get_installer_case_insensitive(self):
        """Test that get_installer is case insensitive."""
        assert get_installer('JAVA') == JavaInstaller
        assert get_installer('Python') == PythonInstaller
    
    def test_get_installer_not_found(self):
        """Test getting non-existent installer."""
        with pytest.raises(ValueError, match='No installer found'):
            get_installer('nonexistent')


class TestBaseInstaller:
    """Tests for BaseInstaller class."""
    
    def test_base_installer_is_abstract(self):
        """Test that BaseInstaller cannot be instantiated."""
        node_config = Mock(spec=NodeConfig)
        software_config = Mock(spec=SoftwareConfig)
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        with pytest.raises(TypeError):
            BaseInstaller(node_config, software_config, ansible_wrapper, logger)
    
    def test_build_inventory(self):
        """Test building Ansible inventory."""
        # Create a concrete subclass for testing
        class TestInstaller(BaseInstaller):
            def pre_check(self): pass
            def install(self): pass
            def post_config(self): pass
            def verify(self): pass
        
        node_config = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            port=22,
            owner_user='testuser',
            owner_pass='testpass',
            super_user='root',
            super_pass='rootpass',
            install=[SoftwareConfig(name='java', version='11', install_path='/opt/java')]
        )
        
        software_config = SoftwareConfig(name='java', version='11', install_path='/opt/java')
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        installer = TestInstaller(node_config, software_config, ansible_wrapper, logger)
        inventory = installer.build_inventory()
        
        assert 'all' in inventory
        assert 'hosts' in inventory['all']
        assert 'test_node' in inventory['all']['hosts']
        
        host_vars = inventory['all']['hosts']['test_node']
        assert host_vars['ansible_host'] == '192.168.1.1'
        assert host_vars['ansible_port'] == 22
        assert host_vars['ansible_user'] == 'testuser'
        assert host_vars['ansible_password'] == 'testpass'
        assert host_vars['ansible_become'] is True
        assert host_vars['ansible_become_password'] == 'rootpass'

    def test_build_inventory_with_keys(self):
        """Test building inventory with SSH keys."""
        class TestInstaller(BaseInstaller):
            def pre_check(self): pass
            def install(self): pass
            def post_config(self): pass
            def verify(self): pass
            
        # Mock os.path.exists and os.stat for SSH keys
        with patch('os.path.exists', return_value=True), \
             patch('os.stat') as mock_stat:
            # Regular file with 0600 permissions (0o100600)
            mock_stat.return_value.st_mode = 0o100600
            node_config = NodeConfig(
                name='test_node',
                host='192.168.1.1',
                owner_user='testuser',
                owner_key='/path/to/owner.key',
                super_user='root',
                super_key='/path/to/super.key',
                install=[SoftwareConfig(name='java', version='11', install_path='/opt/java')]
            )
        
        software_config = SoftwareConfig(name='java', version='11', install_path='/opt/java')
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        installer = TestInstaller(node_config, software_config, ansible_wrapper, logger)
        inventory = installer.build_inventory()
        
        host_vars = inventory['all']['hosts']['test_node']
        assert host_vars['ansible_ssh_private_key_file'] == '/path/to/owner.key'
        assert host_vars['ansible_become_ssh_private_key_file'] == '/path/to/super.key'

    def test_run_command_wrapper(self):
        """Test run_command delegation."""
        class TestInstaller(BaseInstaller):
            def pre_check(self): pass
            def install(self): pass
            def post_config(self): pass
            def verify(self): pass
            
        node_config = NodeConfig(
            name='test_node',
            host='1.1.1.1',
            owner_user='u',
            owner_pass='p',
            super_pass='s',
            install=[SoftwareConfig(name='s', version='v', install_path='/p')]
        )
        software_config = SoftwareConfig(name='s', version='v', install_path='/p')
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        installer = TestInstaller(node_config, software_config, ansible_wrapper, logger)
        installer.run_command('ls -l', become=True)
        
        ansible_wrapper.run_command.assert_called_with(
            host='1.1.1.1',
            command='ls -l',
            user='u',
            password='p',
            ssh_key=None,
            port=22,
            become=True,
            become_user='root',
            become_password='s',
            node_name='test_node',
            check=False
        )


class TestJavaInstaller:
    """Tests for JavaInstaller."""
    
    @pytest.fixture
    def java_installer(self):
        """Create JavaInstaller instance for testing."""
        node_config = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            owner_user='testuser',
            owner_pass='testpass',
            super_pass='rootpass',
            install=[SoftwareConfig(name='java', version='11', install_path='/opt/java')]
        )
        
        software_config = SoftwareConfig(
            name='java',
            version='11',
            install_path='/opt/java',
            source='repository'
        )
        
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        return JavaInstaller(node_config, software_config, ansible_wrapper, logger)
    
    def test_java_installer_initialization(self, java_installer):
        """Test JavaInstaller initialization."""
        assert java_installer.software_config.name == 'java'
        assert java_installer.software_config.version == '11'
        assert java_installer.node_config.name == 'test_node'
    
    def test_pre_check_structure(self, java_installer):
        """Test that pre_check returns expected structure."""
        # Mock run_command to simulate responses
        java_installer.run_command = Mock(side_effect=[
            {'rc': 1, 'stdout': ''},  # Java not installed
            {'rc': 0, 'stdout': '1000M'},  # Disk space check
            {'rc': 0, 'stdout': 'not exists'}  # Install path check
        ])
        
        result = java_installer.pre_check()
        
        assert 'java_installed' in result
        assert 'disk_space_ok' in result
        assert 'install_path_exists' in result
    
    def test_install_calls_playbook(self, java_installer):
        """Test that install method calls run_playbook."""
        # Mock run_playbook
        java_installer.ansible.run_playbook = Mock(return_value={'rc': 0})
        java_installer.get_playbook_path = Mock(return_value='/path/to/install_java.yml')
        
        result = java_installer.install()
        
        # Verify playbook was called
        assert java_installer.ansible.run_playbook.called
        assert result['status'] == 'success'
        assert result['method'] == 'playbook'
        assert result['playbook'] == 'install_java.yml'

    def test_verify_success(self, java_installer):
        """Test successful verification."""
        java_installer.run_command = Mock(return_value={'rc': 0, 'stdout': 'openjdk version "11.0.1"'})
        
        result = java_installer.verify()
        
        assert result['status'] == 'success'
        assert result['verified'] is True
        assert 'openjdk version "11.0.1"' in result['version_output']

    def test_verify_failure(self, java_installer):
        """Test failed verification."""
        java_installer.run_command = Mock(return_value={'rc': 127, 'stdout': 'java: command not found'})
        
        with pytest.raises(InstallException, match='Java command not found'):
            java_installer.verify()


class TestPythonInstaller:
    """Tests for PythonInstaller."""
    
    @pytest.fixture
    def python_installer(self):
        """Create PythonInstaller instance for testing."""
        node_config = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            owner_user='testuser',
            owner_pass='testpass',
            super_pass='rootpass',
            install=[SoftwareConfig(name='python', version='3.9', install_path='/opt/python')]
        )
        
        software_config = SoftwareConfig(
            name='python',
            version='3.9.0',
            install_path='/opt/python',
            source='repository'
        )
        
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        return PythonInstaller(node_config, software_config, ansible_wrapper, logger)
    
    def test_python_installer_initialization(self, python_installer):
        """Test PythonInstaller initialization."""
        assert python_installer.software_config.name == 'python'
        assert python_installer.software_config.version == '3.9.0'
    
    def test_install_calls_playbook(self, python_installer):
        """Test that install method calls run_playbook."""
        # Mock run_playbook
        python_installer.ansible.run_playbook = Mock(return_value={'rc': 0})
        python_installer.get_playbook_path = Mock(return_value='/path/to/install_python.yml')
        
        result = python_installer.install()
        
        # Verify playbook was called
        assert python_installer.ansible.run_playbook.called
        assert result['status'] == 'success'
        assert result['method'] == 'playbook'

    def test_python_pre_check(self, python_installer):
        """Test Python pre-check."""
        python_installer.run_command = Mock(side_effect=[
            {'rc': 0, 'stdout': 'Python 3.9.0'},  # python exists
            {'rc': 0, 'stdout': '1000M'}  # disk space
        ])
        
        result = python_installer.pre_check()
        
        assert result['python_installed'] is True
        assert result['python_version'] == 'Python 3.9.0'
        assert result['disk_space_ok'] is True

    def test_python_verify_success(self, python_installer):
        """Test successful Python verification."""
        python_installer.run_command = Mock(side_effect=[
            {'rc': 0, 'stdout': 'Python 3.9.0'}, # python --version
            {'rc': 0, 'stdout': 'pip 21.0.1'} # pip --version
        ])
        
        result = python_installer.verify()
        
        assert result['status'] == 'success'
        assert result['python_version'] == 'Python 3.9.0'
        assert result['pip_version'] == 'pip 21.0.1'


class TestZookeeperInstaller:
    """Tests for ZookeeperInstaller."""
    
    @pytest.fixture
    def zk_installer(self):
        """Create ZookeeperInstaller instance for testing."""
        node_config = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            owner_user='testuser',
            owner_pass='testpass',
            super_pass='rootpass',
            install=[SoftwareConfig(name='zookeeper', version='3.7.1', install_path='/opt/zookeeper')]
        )
        
        software_config = SoftwareConfig(
            name='zookeeper',
            version='3.7.1',
            install_path='/opt/zookeeper',
            source='repository',
            config={'data_dir': '/var/lib/zookeeper', 'client_port': 2181}
        )
        
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        return ZookeeperInstaller(node_config, software_config, ansible_wrapper, logger)
    
    def test_zookeeper_installer_initialization(self, zk_installer):
        """Test ZookeeperInstaller initialization."""
        assert zk_installer.software_config.name == 'zookeeper'
        assert zk_installer.software_config.version == '3.7.1'
        assert zk_installer.software_config.config['client_port'] == 2181
    
    def test_install_calls_playbook(self, zk_installer):
        """Test that install method calls run_playbook."""
        # Mock run_playbook
        zk_installer.ansible.run_playbook = Mock(return_value={'rc': 0})
        zk_installer.get_playbook_path = Mock(return_value='/path/to/install_zookeeper.yml')
        
        result = zk_installer.install()
        
        # Verify playbook was called
        assert zk_installer.ansible.run_playbook.called
        assert result['status'] == 'success'
        assert result['method'] == 'playbook'

    def test_zookeeper_pre_check(self, zk_installer):
        """Test Zookeeper pre-check."""
        zk_installer.run_command = Mock(side_effect=[
            {'rc': 1, 'stdout': ''}, # not installed
            {'rc': 0, 'stdout': 'openjdk version "11"'}, # java installed
            {'rc': 0, 'stdout': '1000M'} # disk space
        ])
        
        result = zk_installer.pre_check()
        
        assert result['zookeeper_installed'] is False
        assert result['java_installed'] is True
        assert result['disk_space_ok'] is True

    def test_zookeeper_verify_success(self, zk_installer):
        """Test successful Zookeeper verification."""
        zk_installer.run_command = Mock(side_effect=[
            {'rc': 0, 'stdout': 'found'}, # binary found
            {'rc': 0, 'stdout': 'ZooKeeper JLine enabled'} # version output
        ])
        
        result = zk_installer.verify()
        
        assert result['status'] == 'success'
        assert result['verified'] is True
        assert 'ZooKeeper JLine enabled' in result['version_info']
