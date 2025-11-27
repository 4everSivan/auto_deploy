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
            install=[SoftwareConfig('java', '11', '/opt/java')]
        )
        
        software_config = SoftwareConfig('java', '11', '/opt/java')
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
            install=[SoftwareConfig('java', '11', '/opt/java')]
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
            install=[SoftwareConfig('python', '3.9', '/opt/python')]
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
            install=[SoftwareConfig('zookeeper', '3.7.1', '/opt/zookeeper')]
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
