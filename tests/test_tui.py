"""
Unit tests for the Auto Deploy TUI.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from textual.widgets import Header, Footer, ProgressBar
from deployer.tui.app import AutoDeployApp
from deployer.tui.widgets import NodeStatusTree, ProgressPanel, TaskDetailsPanel, LogViewPanel
from deployer.executor import DeploymentExecutor
from deployer.task_manager import Task, TaskStatus

@pytest.fixture
def mock_executor():
    """Create a mock DeploymentExecutor."""
    executor = Mock(spec=DeploymentExecutor)
    executor.config = Mock()
    executor.task_manager = Mock()
    executor.logger = Mock()
    executor.logger.main_logger = Mock()
    executor.logger.node_loggers = {}
    
    # Setup default return values for task_manager.get_stats
    executor.task_manager.get_stats.return_value = {
        'total_tasks': 10,
        'tasks_completed': 2,
        'tasks_failed': 1,
        'total_nodes': 3,
        'nodes_completed': 1,
        'percent_complete': 25.0
    }
    
    executor.config.get_nodes.return_value = []
    executor.is_running.return_value = False
    
    return executor

@pytest.mark.asyncio
async def test_app_initialization(mock_executor):
    """Test that the app initializes with correct components."""
    app = AutoDeployApp(mock_executor, config_name="test_config.yml")
    
    async with app.run_test() as pilot:
        # Check basic properties
        assert app.title == "Auto Deploy v0.1.0"
        assert "test_config.yml" in app.sub_title
        
        # Verify layout components exist
        assert pilot.app.query_one(Header)
        assert pilot.app.query_one(Footer)
        assert pilot.app.query_one(NodeStatusTree)
        assert pilot.app.query_one(ProgressPanel)
        assert pilot.app.query_one(TaskDetailsPanel)
        assert pilot.app.query_one(LogViewPanel)

@pytest.mark.asyncio
async def test_progress_panel_updates(mock_executor):
    """Test that the progress panel updates its stats correctly."""
    app = AutoDeployApp(mock_executor)
    
    async with app.run_test() as pilot:
        panel = pilot.app.query_one(ProgressPanel)
        
        # Initial update happens on mount
        assert panel.progress == 25.0
        
        # Trigger an update with new stats
        mock_executor.task_manager.get_stats.return_value = {
            'total_tasks': 10,
            'tasks_completed': 5,
            'tasks_failed': 0,
            'total_nodes': 3,
            'nodes_completed': 2,
            'percent_complete': 50.0
        }
        
        # Manually trigger the update method
        pilot.app._update_progress()
        await pilot.pause()
        
        assert panel.progress == 50.0
        assert "Nodes:   2/3 completed" in pilot.app.query_one("#stats-content").renderable

@pytest.mark.asyncio
async def test_task_details_reactive(mock_executor):
    """Test that name details panel updates when current_task changes."""
    app = AutoDeployApp(mock_executor)
    
    async with app.run_test() as pilot:
        panel = pilot.app.query_one(TaskDetailsPanel)
        assert "No active task" in pilot.app.query_one("#details-content").renderable
        
        test_task = Task(
            task_id="node1_java_11",
            node_name="node1",
            software_name="java",
            software_version="11",
            status=TaskStatus.RUNNING
        )
        
        # Set the reactive property directly
        panel.current_task = test_task
        await pilot.pause()
        
        content = pilot.app.query_one("#details-content").renderable
        assert "Node: node1" in content
        assert "Software: java" in content
        assert "Status: running" in content

@pytest.mark.asyncio
async def test_action_start_behavior(mock_executor):
    """Test the start action behavior."""
    app = AutoDeployApp(mock_executor)
    
    async with app.run_test() as pilot:
        # Ensure it's not started yet
        assert app.start_time is None
        
        # Mock executor to be NOT running
        mock_executor.is_running.return_value = False
        
        # Press 's' to start
        await pilot.press("s")
        await pilot.pause()
        
        assert app.start_time is not None
        # Verify executor.execute_all was likely called (it runs in a thread, so we check if Thread.start was called if we could, 
        # but here we just check if start_time was set)
        
        # Press 's' again, should trigger notification but not reset start_time
        mock_executor.is_running.return_value = True
        old_start_time = app.start_time
        await pilot.press("s")
        await pilot.pause()
        assert app.start_time == old_start_time

@pytest.mark.asyncio
async def test_help_modal(mock_executor):
    """Test that help screen can be opened and closed."""
    app = AutoDeployApp(mock_executor)
    
    async with app.run_test() as pilot:
        # Press '?' to open help
        await pilot.press("?")
        await pilot.pause()
        
        # Check if HelpScreen is active
        from deployer.tui.app import HelpScreen
        assert isinstance(pilot.app.screen, HelpScreen)
        
        # Press any key to close
        await pilot.press("escape")
        await pilot.pause()
        
        # Should be back to main screen
        assert not isinstance(pilot.app.screen, HelpScreen)
