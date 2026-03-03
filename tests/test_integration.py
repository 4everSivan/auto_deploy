"""
Integration tests for Auto Deploy.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import yaml

from deployer.config import Config
from deployer.task_manager import TaskManager, TaskStatus
from deployer.executor import DeploymentExecutor
from common.logger import DeployLogger

@pytest.fixture
def mock_config_file(tmp_path):
    """Create a temporary config file."""
    config_data = {
        'max_concurrent_nodes': 2,
        'nodes': [
            {
                'node1': {
                    'host': '192.168.1.1',
                    'owner_user': 'user1',
                    'owner_pass': 'pass1',
                    'super_user': 'root',
                    'super_pass': 'root1',
                    'install': [
                        {'java': {'version': '11', 'install_path': '/opt/java'}}
                    ]
                }
            },
            {
                'node2': {
                    'host': '192.168.1.2',
                    'owner_user': 'user2',
                    'owner_pass': 'pass2',
                    'super_user': 'root',
                    'super_pass': 'root2',
                    'install': [
                        {'python': {'version': '3.9', 'install_path': '/opt/python'}}
                    ]
                }
            }
        ]
    }
    
    config_file = tmp_path / "test_config.yml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
        
    return str(config_file)

@patch('deployer.executor.DeploymentExecutor._run_checkers')
@patch('deployer.installers.java_installer.JavaInstaller.install')
@patch('deployer.installers.java_installer.JavaInstaller.verify')
@patch('deployer.installers.python_installer.PythonInstaller.install')
@patch('deployer.installers.python_installer.PythonInstaller.verify')
@patch('ansible_runner.run')
def test_full_deployment_pipeline(
    mock_ansible_run,
    mock_python_verify,
    mock_python_install,
    mock_java_verify,
    mock_java_install,
    mock_run_checkers,
    mock_config_file,
    tmp_path
):
    """Test the full deployment pipeline from config to execution."""
    mock_run_checkers.return_value = {'failed': 0, 'passed': 5}
    mock_java_install.return_value = {'status': 'success'}
    mock_java_verify.return_value = {'status': 'success'} # Fixed: return dict
    mock_python_install.return_value = {'status': 'success'}
    mock_python_verify.return_value = {'status': 'success'} # Fixed: return dict
    
    config = Config(mock_config_file)
    task_manager = TaskManager(config)
    task_manager.create_tasks()
    
    logger = DeployLogger(str(tmp_path / "logs"))
    executor = DeploymentExecutor(config, task_manager, logger)
    
    starts = []
    completes = []
    
    def on_start(task): starts.append(task.task_id)
    def on_complete(task): completes.append(task.task_id)
    
    executor.register_callback('on_task_start', on_start)
    executor.register_callback('on_task_complete', on_complete)
    
    executor.execute_all()
    executor.wait_completion(timeout=10)
    
    stats = task_manager.get_stats()
    assert stats['total_tasks'] == 2
    assert stats['tasks_completed'] == 2
    
    assert 'node1_java_11' in starts
    assert 'node2_python_3.9' in starts

@patch('deployer.executor.DeploymentExecutor._run_checkers')
@patch('deployer.installers.java_installer.JavaInstaller.install')
def test_deployment_with_check_failure(
    mock_java_install,
    mock_run_checkers,
    mock_config_file,
    tmp_path
):
    """Test deployment stopping on pre-check failure."""
    mock_run_checkers.return_value = {'failed': 1, 'passed': 0}
    
    config = Config(mock_config_file)
    task_manager = TaskManager(config)
    task_manager.create_tasks()
    
    logger = DeployLogger(str(tmp_path / "logs"))
    executor = DeploymentExecutor(config, task_manager, logger)
    
    executor.execute_all()
    executor.wait_completion(timeout=10)
    
    stats = task_manager.get_stats()
    assert stats['tasks_failed'] == 2

@patch('deployer.executor.DeploymentExecutor._run_checkers')
@patch('deployer.executor.DeploymentExecutor._get_installer')
def test_deployment_cancellation(
    mock_get_installer,
    mock_run_checkers,
    mock_config_file,
    tmp_path
):
    """Test stopping a deployment mid-execution."""
    mock_run_checkers.return_value = {'failed': 0, 'passed': 5}
    
    mock_installer = Mock()
    def slow_install(*args, **kwargs):
        import time
        time.sleep(0.5)
        return {'status': 'success'}
    mock_installer.install.side_effect = slow_install
    mock_installer.verify.return_value = {'status': 'success'} # Fixed: return dict
    mock_get_installer.return_value = mock_installer
    
    config = Config(mock_config_file)
    task_manager = TaskManager(config)
    task_manager.create_tasks()
    
    logger = DeployLogger(str(tmp_path / "logs"))
    executor = DeploymentExecutor(config, task_manager, logger)
    
    import threading
    t = threading.Thread(target=executor.execute_all)
    t.start()
    
    import time
    time.sleep(0.1)
    
    executor.stop()
    executor.wait_completion(timeout=10)
    
    stats = task_manager.get_statistics()
    assert (stats['completed'] + stats['failed'] + stats['skipped'] + stats['running']) > 0
