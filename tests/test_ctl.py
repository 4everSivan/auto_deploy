"""
Tests for CLI interface in ctl.py.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from deployer.ctl import ctl

@pytest.fixture
def runner():
    return CliRunner()

@patch('deployer.ctl.Config')
@patch('deployer.ctl.DeploymentExecutor')
@patch('deployer.ctl.TaskManager')
@patch('deployer.ctl.CLIUI')
def test_deploy_command_basic(mock_ui_class, mock_task_manager_class, mock_executor_class, mock_config_class, runner):
    """Test the basic deploy command execution."""
    # Mock config
    mock_config = MagicMock()
    mock_config.get_log_dir.return_value = '/tmp/logs'
    mock_config.get_log_level.return_value = 'INFO'
    mock_config.get_nodes.return_value = []
    mock_config_class.return_value = mock_config
    
    # Mock UI
    mock_ui = MagicMock()
    mock_ui.confirm_deployment.return_value = True
    mock_ui_class.return_value = mock_ui
    
    # Mock TaskManager
    mock_task_manager = MagicMock()
    mock_task_manager.get_statistics.return_value = {
        'total': 0, 'completed': 0, 'failed': 0, 'skipped': 0
    }
    mock_task_manager_class.return_value = mock_task_manager
    
    # Run command
    result = runner.invoke(ctl, ['--config-file', 'test.yml', 'deploy', '--yes'])
    
    assert result.exit_code == 0
    mock_executor_class.assert_called_once()
    mock_executor_class.return_value.execute_all.assert_called_once()
    mock_executor_class.return_value.wait_completion.assert_called_once()
    mock_ui.print_banner.assert_called_once()

@patch('deployer.ctl.Config')
@patch('deployer.ctl.DeploymentExecutor')
@patch('deployer.ctl.TaskManager')
@patch('deployer.ctl.CLIUI')
def test_deploy_dry_run(mock_ui_class, mock_task_manager_class, mock_executor_class, mock_config_class, runner):
    """Test the deploy command with --dry-run."""
    mock_config = MagicMock()
    mock_config.get_log_dir.return_value = '/tmp/logs'
    mock_config.get_log_level.return_value = 'INFO'
    mock_config.get_nodes.return_value = []
    mock_config_class.return_value = mock_config
    
    mock_task_manager = MagicMock()
    mock_task_manager.get_statistics.return_value = {
        'total': 0, 'completed': 0, 'failed': 0, 'skipped': 0
    }
    mock_task_manager_class.return_value = mock_task_manager
    
    result = runner.invoke(ctl, ['deploy', '--dry-run'])
    
    assert result.exit_code == 0
    # Check if dry_run was passed to Executor
    args, kwargs = mock_executor_class.call_args
    assert kwargs['dry_run'] is True
    mock_ui_class.return_value.print_dry_run_warning.assert_called_once()

def test_version_command(runner):
    """Test version command."""
    result = runner.invoke(ctl, ['version'])
    assert result.exit_code == 0
    assert 'Auto-deploy version' in result.output
