"""
Tests for checker system.
"""

import pytest
from unittest.mock import Mock, MagicMock

from deployer.checker import (
    BaseChecker, CheckResult, CheckStatus, CheckerManager,
    ConnectivityChecker, DiskSpaceChecker, MemoryChecker,
    PortAvailabilityChecker, SystemInfoChecker,
    PackageManagerChecker, SudoPrivilegeChecker
)
from deployer.models import NodeConfig, SoftwareConfig
from deployer.ansible_wrapper import AnsibleWrapper
from common.logger import DeployLogger
from common.exceptions import ConnectionException


class TestCheckResult:
    """Tests for CheckResult class."""
    
    def test_check_result_creation(self):
        """Test creating a check result."""
        result = CheckResult(
            name='Test Check',
            status=CheckStatus.PASSED,
            message='Test passed',
            details={'key': 'value'}
        )
        
        assert result.name == 'Test Check'
        assert result.status == CheckStatus.PASSED
        assert result.message == 'Test passed'
        assert result.details == {'key': 'value'}
    
    def test_check_result_to_dict(self):
        """Test converting check result to dictionary."""
        result = CheckResult(
            name='Test Check',
            status=CheckStatus.FAILED,
            message='Test failed'
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['name'] == 'Test Check'
        assert result_dict['status'] == 'failed'
        assert result_dict['message'] == 'Test failed'
        assert 'details' in result_dict


class TestCheckerManager:
    """Tests for CheckerManager."""
    
    @pytest.fixture
    def checker_manager(self):
        """Create checker manager for testing."""
        node_config = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            owner_user='testuser',
            owner_pass='testpass',
            super_pass='rootpass',
            install=[SoftwareConfig('java', '11', '/opt/java')]
        )
        
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        return CheckerManager(node_config, ansible_wrapper, logger)
    
    def test_add_checker(self, checker_manager):
        """Test adding checkers."""
        checker = Mock(spec=BaseChecker)
        checker_manager.add_checker(checker)
        
        assert len(checker_manager.checkers) == 1
        assert checker_manager.checkers[0] == checker
    
    def test_run_all_passed(self, checker_manager):
        """Test running all checkers with passed results."""
        checker1 = Mock(spec=BaseChecker)
        checker1.check.return_value = CheckResult(
            'Check 1', CheckStatus.PASSED, 'Passed'
        )
        
        checker2 = Mock(spec=BaseChecker)
        checker2.check.return_value = CheckResult(
            'Check 2', CheckStatus.PASSED, 'Passed'
        )
        
        checker_manager.add_checker(checker1)
        checker_manager.add_checker(checker2)
        
        summary = checker_manager.run_all()
        
        assert summary['total'] == 2
        assert summary['passed'] == 2
        assert summary['failed'] == 0
        assert summary['warnings'] == 0
    
    def test_run_all_mixed_results(self, checker_manager):
        """Test running checkers with mixed results."""
        checker1 = Mock(spec=BaseChecker)
        checker1.check.return_value = CheckResult(
            'Check 1', CheckStatus.PASSED, 'Passed'
        )
        
        checker2 = Mock(spec=BaseChecker)
        checker2.check.return_value = CheckResult(
            'Check 2', CheckStatus.WARNING, 'Warning'
        )
        
        checker3 = Mock(spec=BaseChecker)
        checker3.check.return_value = CheckResult(
            'Check 3', CheckStatus.FAILED, 'Failed'
        )
        
        checker_manager.add_checker(checker1)
        checker_manager.add_checker(checker2)
        checker_manager.add_checker(checker3)
        
        summary = checker_manager.run_all()
        
        assert summary['total'] == 3
        assert summary['passed'] == 1
        assert summary['warnings'] == 1
        assert summary['failed'] == 1


class TestConnectivityChecker:
    """Tests for ConnectivityChecker."""
    
    @pytest.fixture
    def connectivity_checker(self):
        """Create connectivity checker for testing."""
        node_config = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            owner_user='testuser',
            owner_pass='testpass',
            super_pass='rootpass',
            install=[SoftwareConfig('java', '11', '/opt/java')]
        )
        
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        return ConnectivityChecker(node_config, ansible_wrapper, logger)
    
    def test_connectivity_check_success(self, connectivity_checker):
        """Test successful connectivity check."""
        connectivity_checker.ansible.test_connection = Mock(return_value=True)
        
        result = connectivity_checker.check()
        
        assert result.status == CheckStatus.PASSED
        assert 'Successfully connected' in result.message
    
    def test_connectivity_check_failure(self, connectivity_checker):
        """Test failed connectivity check."""
        connectivity_checker.ansible.test_connection = Mock(
            side_effect=ConnectionException('Connection refused')
        )
        
        result = connectivity_checker.check()
        
        assert result.status == CheckStatus.FAILED
        assert 'Failed to connect' in result.message


class TestDiskSpaceChecker:
    """Tests for DiskSpaceChecker."""
    
    @pytest.fixture
    def disk_checker(self):
        """Create disk space checker for testing."""
        node_config = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            owner_user='testuser',
            owner_pass='testpass',
            super_pass='rootpass',
            install=[SoftwareConfig('java', '11', '/opt/java')]
        )
        
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        return DiskSpaceChecker(
            node_config, ansible_wrapper, logger, min_space_mb=1024
        )
    
    def test_disk_space_sufficient(self, disk_checker):
        """Test sufficient disk space."""
        disk_checker.run_command = Mock(return_value={
            'rc': 0,
            'stdout': '2048M'
        })
        
        result = disk_checker.check()
        
        assert result.status == CheckStatus.PASSED
        assert 'Sufficient disk space' in result.message
    
    def test_disk_space_insufficient(self, disk_checker):
        """Test insufficient disk space."""
        disk_checker.run_command = Mock(return_value={
            'rc': 0,
            'stdout': '512M'
        })
        
        result = disk_checker.check()
        
        assert result.status == CheckStatus.FAILED
        assert 'Insufficient disk space' in result.message


class TestMemoryChecker:
    """Tests for MemoryChecker."""
    
    @pytest.fixture
    def memory_checker(self):
        """Create memory checker for testing."""
        node_config = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            owner_user='testuser',
            owner_pass='testpass',
            super_pass='rootpass',
            install=[SoftwareConfig('java', '11', '/opt/java')]
        )
        
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        return MemoryChecker(
            node_config, ansible_wrapper, logger, min_memory_mb=512
        )
    
    def test_memory_sufficient(self, memory_checker):
        """Test sufficient memory."""
        memory_checker.run_command = Mock(return_value={
            'rc': 0,
            'stdout': '1024'
        })
        
        result = memory_checker.check()
        
        assert result.status == CheckStatus.PASSED
        assert 'Sufficient memory' in result.message


class TestPortAvailabilityChecker:
    """Tests for PortAvailabilityChecker."""
    
    @pytest.fixture
    def port_checker(self):
        """Create port availability checker for testing."""
        node_config = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            owner_user='testuser',
            owner_pass='testpass',
            super_pass='rootpass',
            install=[SoftwareConfig('java', '11', '/opt/java')]
        )
        
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        return PortAvailabilityChecker(
            node_config, ansible_wrapper, logger, ports=[8080, 9090]
        )
    
    def test_ports_available(self, port_checker):
        """Test all ports available."""
        port_checker.run_command = Mock(return_value={
            'rc': 0,
            'stdout': 'free'
        })
        
        result = port_checker.check()
        
        assert result.status == CheckStatus.PASSED
        assert 'All required ports are available' in result.message
    
    def test_no_ports_to_check(self):
        """Test with no ports specified."""
        node_config = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            owner_user='testuser',
            owner_pass='testpass',
            super_pass='rootpass',
            install=[SoftwareConfig('java', '11', '/opt/java')]
        )
        
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        checker = PortAvailabilityChecker(
            node_config, ansible_wrapper, logger, ports=[]
        )
        
        result = checker.check()
        
        assert result.status == CheckStatus.SKIPPED


class TestSystemInfoChecker:
    """Tests for SystemInfoChecker."""
    
    @pytest.fixture
    def system_checker(self):
        """Create system info checker for testing."""
        node_config = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            owner_user='testuser',
            owner_pass='testpass',
            super_pass='rootpass',
            install=[SoftwareConfig('java', '11', '/opt/java')]
        )
        
        ansible_wrapper = Mock(spec=AnsibleWrapper)
        logger = Mock(spec=DeployLogger)
        
        return SystemInfoChecker(node_config, ansible_wrapper, logger)
    
    def test_system_info_collection(self, system_checker):
        """Test system info collection."""
        system_checker.run_command = Mock(side_effect=[
            {'rc': 0, 'stdout': 'PRETTY_NAME="Ubuntu 20.04"\nID=ubuntu'},
            {'rc': 0, 'stdout': '5.4.0-42-generic'},
            {'rc': 0, 'stdout': '4'},
            {'rc': 0, 'stdout': '8192'}
        ])
        
        result = system_checker.check()
        
        assert result.status == CheckStatus.PASSED
        assert 'System:' in result.message
