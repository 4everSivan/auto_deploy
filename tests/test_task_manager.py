"""
Tests for deployer.task_manager module.
"""

import pytest
from unittest.mock import Mock

from deployer.task_manager import Task, TaskStatus, TaskManager
from deployer.config import Config
from deployer.models import NodeConfig, SoftwareConfig


class TestTask:
    """Tests for Task class."""
    
    def test_task_initialization(self):
        """Test task initialization."""
        task = Task(
            task_id='node1_java_11',
            node_name='node1',
            software_name='java',
            software_version='11'
        )
        
        assert task.task_id == 'node1_java_11'
        assert task.node_name == 'node1'
        assert task.software_name == 'java'
        assert task.software_version == '11'
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0
        assert task.start_time is None
        assert task.end_time is None
    
    def test_task_start(self):
        """Test task start."""
        task = Task('test', 'node1', 'java', '11')
        task.start()
        
        assert task.status == TaskStatus.RUNNING
        assert task.start_time is not None
        assert task.progress == 0.0
    
    def test_task_complete(self):
        """Test task completion."""
        task = Task('test', 'node1', 'java', '11')
        task.start()
        task.complete()
        
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100.0
        assert task.end_time is not None
    
    def test_task_fail(self):
        """Test task failure."""
        task = Task('test', 'node1', 'java', '11')
        task.start()
        task.fail('Installation failed')
        
        assert task.status == TaskStatus.FAILED
        assert task.error_message == 'Installation failed'
        assert task.end_time is not None
    
    def test_task_skip(self):
        """Test task skip."""
        task = Task('test', 'node1', 'java', '11')
        task.skip('Stopped by user')
        
        assert task.status == TaskStatus.SKIPPED
        assert task.error_message == 'Stopped by user'
    
    def test_task_update_progress(self):
        """Test progress update."""
        task = Task('test', 'node1', 'java', '11')
        task.update_progress(50.0)
        
        assert task.progress == 50.0
        
        # Test bounds
        task.update_progress(150.0)
        assert task.progress == 100.0
        
        task.update_progress(-10.0)
        assert task.progress == 0.0
    
    def test_task_get_duration(self):
        """Test duration calculation."""
        task = Task('test', 'node1', 'java', '11')
        
        # No duration before start
        assert task.get_duration() is None
        
        task.start()
        duration = task.get_duration()
        assert duration is not None
        assert duration >= 0
        
        task.complete()
        duration = task.get_duration()
        assert duration is not None
        assert duration >= 0
    
    def test_task_to_dict(self):
        """Test conversion to dictionary."""
        task = Task('test', 'node1', 'java', '11')
        task.start()
        task.update_progress(50.0)
        
        task_dict = task.to_dict()
        
        assert task_dict['task_id'] == 'test'
        assert task_dict['node_name'] == 'node1'
        assert task_dict['software_name'] == 'java'
        assert task_dict['status'] == 'running'
        assert task_dict['progress'] == 50.0


class TestTaskManager:
    """Tests for TaskManager class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=Config)
        
        # Create mock nodes
        node1 = NodeConfig(
            name='node1',
            host='192.168.1.1',
            owner_user='user1',
            owner_pass='pass1',
            super_pass='root1',
            install=[
                SoftwareConfig('java', '11', '/opt/java'),
                SoftwareConfig('python', '3.9', '/opt/python')
            ]
        )
        
        node2 = NodeConfig(
            name='node2',
            host='192.168.1.2',
            owner_user='user2',
            owner_pass='pass2',
            super_pass='root2',
            install=[
                SoftwareConfig('zookeeper', '3.7.1', '/opt/zookeeper')
            ]
        )
        
        config.get_nodes.return_value = [node1, node2]
        
        return config
    
    def test_task_manager_initialization(self, mock_config):
        """Test task manager initialization."""
        manager = TaskManager(mock_config)
        
        assert manager.config == mock_config
        assert len(manager.tasks) == 0
        assert len(manager.node_tasks) == 0
    
    def test_create_tasks(self, mock_config):
        """Test task creation."""
        manager = TaskManager(mock_config)
        manager.create_tasks()
        
        # Should create 3 tasks total (2 for node1, 1 for node2)
        assert len(manager.tasks) == 3
        assert len(manager.node_tasks) == 2
        
        # Check node1 tasks
        node1_tasks = manager.get_node_tasks('node1')
        assert len(node1_tasks) == 2
        assert node1_tasks[0].software_name in ['java', 'python']
        assert node1_tasks[1].software_name in ['java', 'python']
        
        # Check node2 tasks
        node2_tasks = manager.get_node_tasks('node2')
        assert len(node2_tasks) == 1
        assert node2_tasks[0].software_name == 'zookeeper'
    
    def test_get_task(self, mock_config):
        """Test getting task by ID."""
        manager = TaskManager(mock_config)
        manager.create_tasks()
        
        # Get a task
        task_id = list(manager.tasks.keys())[0]
        task = manager.get_task(task_id)
        
        assert task is not None
        assert task.task_id == task_id
        
        # Non-existent task
        assert manager.get_task('nonexistent') is None
    
    def test_get_all_tasks(self, mock_config):
        """Test getting all tasks."""
        manager = TaskManager(mock_config)
        manager.create_tasks()
        
        all_tasks = manager.get_all_tasks()
        assert len(all_tasks) == 3
    
    def test_get_statistics(self, mock_config):
        """Test statistics calculation."""
        manager = TaskManager(mock_config)
        manager.create_tasks()
        
        stats = manager.get_statistics()
        
        assert stats['total'] == 3
        assert stats['pending'] == 3
        assert stats['running'] == 0
        assert stats['completed'] == 0
        assert stats['failed'] == 0
        assert stats['skipped'] == 0
        
        # Update some task statuses
        tasks = manager.get_all_tasks()
        tasks[0].start()
        tasks[1].complete()
        tasks[2].fail('Error')
        
        stats = manager.get_statistics()
        assert stats['running'] == 1
        assert stats['completed'] == 1
        assert stats['failed'] == 1
    
    def test_get_progress(self, mock_config):
        """Test overall progress calculation."""
        manager = TaskManager(mock_config)
        manager.create_tasks()
        
        # Initial progress
        assert manager.get_progress() == 0.0
        
        # Update progress
        tasks = manager.get_all_tasks()
        tasks[0].update_progress(100.0)
        tasks[1].update_progress(50.0)
        tasks[2].update_progress(0.0)
        
        # Average: (100 + 50 + 0) / 3 = 50
        assert manager.get_progress() == 50.0
    
    def test_reset(self, mock_config):
        """Test task reset."""
        manager = TaskManager(mock_config)
        manager.create_tasks()
        
        # Modify tasks
        tasks = manager.get_all_tasks()
        tasks[0].start()
        tasks[0].complete()
        tasks[1].fail('Error')
        
        # Reset
        manager.reset()
        
        # All tasks should be pending
        for task in manager.get_all_tasks():
            assert task.status == TaskStatus.PENDING
            assert task.progress == 0.0
            assert task.start_time is None
            assert task.end_time is None
            assert task.error_message is None
