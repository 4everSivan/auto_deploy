"""
Tests for deployer.executor module.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import threading
import time

from deployer.executor import DeploymentExecutor
from deployer.task_manager import TaskManager, Task, TaskStatus
from deployer.config import Config
from deployer.models import NodeConfig, SoftwareConfig
from common.logger import DeployLogger


class TestDeploymentExecutor:
    """Tests for DeploymentExecutor class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=Config)
        config.get_max_concurrent_nodes.return_value = 2
        
        node1 = NodeConfig(
            name='node1',
            host='192.168.1.1',
            owner_user='user1',
            owner_pass='pass1',
            super_pass='root1',
            install=[SoftwareConfig('java', '11', '/opt/java')]
        )
        
        config.get_nodes.return_value = [node1]
        return config
    
    @pytest.fixture
    def task_manager(self, mock_config):
        """Create task manager."""
        manager = TaskManager(mock_config)
        manager.create_tasks()
        return manager
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return Mock(spec=DeployLogger)
    
    @pytest.fixture
    def executor(self, mock_config, task_manager, mock_logger):
        """Create executor instance."""
        return DeploymentExecutor(mock_config, task_manager, mock_logger)
    
    def test_executor_initialization(self, executor, mock_config, task_manager):
        """Test executor initialization."""
        assert executor.config == mock_config
        assert executor.task_manager == task_manager
        assert executor.max_workers == 2
        assert not executor.stop_event.is_set()
        assert executor.pause_event.is_set()  # Not paused initially
    
    def test_register_callback(self, executor):
        """Test callback registration."""
        callback = Mock()
        executor.register_callback('on_task_start', callback)
        
        assert 'on_task_start' in executor.callbacks
        assert callback in executor.callbacks['on_task_start']
    
    def test_trigger_callback(self, executor):
        """Test callback triggering."""
        callback = Mock()
        executor.register_callback('on_task_start', callback)
        
        task = Mock()
        executor._trigger_callback('on_task_start', task)
        
        callback.assert_called_once_with(task)
    
    def test_pause_resume(self, executor):
        """Test pause and resume functionality."""
        assert not executor.is_paused()
        
        executor.pause()
        assert executor.is_paused()
        
        executor.resume()
        assert not executor.is_paused()
    
    def test_stop(self, executor):
        """Test stop functionality."""
        assert not executor.is_stopped()
        
        executor.stop()
        assert executor.is_stopped()
    
    def test_get_software_config(self, executor):
        """Test getting software configuration."""
        node = NodeConfig(
            name='test',
            host='192.168.1.1',
            owner_user='user',
            owner_pass='pass',
            super_pass='root',
            install=[
                SoftwareConfig('java', '11', '/opt/java'),
                SoftwareConfig('python', '3.9', '/opt/python')
            ]
        )
        
        java_config = executor._get_software_config(node, 'java')
        assert java_config.name == 'java'
        assert java_config.version == '11'
        
        python_config = executor._get_software_config(node, 'python')
        assert python_config.name == 'python'
        
        # Non-existent software
        with pytest.raises(ValueError, match='not found'):
            executor._get_software_config(node, 'nonexistent')
    
    @patch('deployer.installers.get_installer')
    def test_get_installer(self, mock_get_installer, executor):
        """Test getting installer instance."""
        mock_installer_class = Mock()
        mock_get_installer.return_value = mock_installer_class
        
        node = Mock(spec=NodeConfig)
        software = Mock(spec=SoftwareConfig)
        
        executor._get_installer('java', node, software)
        
        mock_get_installer.assert_called_once_with('java')
        mock_installer_class.assert_called_once()
    
    def test_has_check_errors(self, executor):
        """Test error detection in check results."""
        # No errors
        results = {'failed': 0, 'passed': 5}
        assert not executor._has_check_errors(results)
        
        # Has errors
        results = {'failed': 2, 'passed': 3}
        assert executor._has_check_errors(results)
    
    @patch('deployer.checker.CheckerManager')
    @patch('deployer.checker.ConnectivityChecker')
    @patch('deployer.checker.DiskSpaceChecker')
    @patch('deployer.checker.MemoryChecker')
    @patch('deployer.checker.SystemInfoChecker')
    def test_run_checkers(
        self,
        mock_system_info,
        mock_memory,
        mock_disk,
        mock_connectivity,
        mock_checker_manager_class,
        executor
    ):
        """Test running checkers."""
        mock_manager = Mock()
        mock_manager.run_all.return_value = {'failed': 0, 'passed': 4}
        mock_checker_manager_class.return_value = mock_manager
        
        node = Mock(spec=NodeConfig)
        software = Mock(spec=SoftwareConfig)
        
        results = executor._run_checkers(node, software)
        
        assert results['failed'] == 0
        assert results['passed'] == 4
        mock_manager.run_all.assert_called_once()
