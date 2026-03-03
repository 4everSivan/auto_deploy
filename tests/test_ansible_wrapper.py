"""
Tests for deployer.ansible_wrapper module.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from deployer.ansible_wrapper import AnsibleWrapper
from common.exceptions import AnsibleException, ConnectionException
from common.logger import DeployLogger

class TestAnsibleWrapper:
    """Tests for AnsibleWrapper class."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return Mock(spec=DeployLogger)
    
    @pytest.fixture
    def ansible(self, mock_logger):
        """Create AnsibleWrapper instance."""
        return AnsibleWrapper(mock_logger)
    
    @patch('ansible_runner.run')
    def test_run_playbook_success(self, mock_run, ansible, tmp_path):
        """Test successful playbook execution."""
        # Setup mock result
        mock_result = MagicMock()
        mock_result.status = 'successful'
        mock_result.rc = 0
        mock_result.stats = {'ok': 1}
        mock_run.return_value = mock_result
        
        # Create a dummy playbook file
        playbook_path = tmp_path / "test_playbook.yml"
        playbook_path.write_text("---")
        
        inventory = {'all': {'hosts': {'localhost': {}}}}
        
        result = ansible.run_playbook(
            playbook=str(playbook_path),
            inventory=inventory,
            node_name='test_node'
        )
        
        assert result['status'] == 'success'
        assert result['rc'] == 0
        assert result['stats'] == {'ok': 1}
        mock_run.assert_called_once()
    
    def test_run_playbook_not_found(self, ansible):
        """Test playbook not found."""
        with pytest.raises(AnsibleException, match='Playbook not found'):
            ansible.run_playbook('/nonexistent.yml', {})
    
    @patch('ansible_runner.run')
    def test_run_playbook_failure(self, mock_run, ansible, tmp_path):
        """Test failed playbook execution."""
        # Setup mock result
        mock_result = MagicMock()
        mock_result.status = 'failed'
        mock_result.rc = 1
        mock_result.events = [
            {'event': 'runner_on_failed', 'event_data': {'res': {'msg': 'error details'}}}
        ]
        mock_run.return_value = mock_result
        
        playbook_path = tmp_path / "test_playbook.yml"
        playbook_path.write_text("---")
        
        with pytest.raises(AnsibleException, match='Playbook failed with status: failed'):
            ansible.run_playbook(str(playbook_path), {})
    
    @patch('ansible_runner.run')
    def test_run_command_success(self, mock_run, ansible):
        """Test successful ad-hoc command execution."""
        # Setup mock result
        mock_result = MagicMock()
        mock_result.status = 'successful'
        mock_result.events = [
            {
                'event': 'runner_on_ok',
                'event_data': {'res': {'stdout': 'hello world', 'rc': 0}}
            }
        ]
        mock_run.return_value = mock_result
        
        result = ansible.run_command(
            host='localhost',
            command='echo hello world',
            user='testuser',
            password='testpassword'
        )
        
        assert result['status'] == 'success'
        assert result['stdout'] == 'hello world'
        assert result['rc'] == 0
    
    def test_run_command_no_auth(self, ansible):
        """Test run_command without password or ssh_key."""
        with pytest.raises(AnsibleException, match='Either password or ssh_key must be provided'):
            ansible.run_command('localhost', 'ls', 'user')
    
    @patch('ansible_runner.run')
    def test_test_connection_success(self, mock_run, ansible):
        """Test successful connection test."""
        mock_result = MagicMock()
        mock_result.status = 'successful'
        mock_result.events = [
            {'event': 'runner_on_ok', 'event_data': {'res': {'rc': 0, 'stdout': 'test'}}}
        ]
        mock_run.return_value = mock_result
        
        assert ansible.test_connection('localhost', 'user', 'pass') is True
    
    @patch('ansible_runner.run')
    def test_test_connection_failure(self, mock_run, ansible):
        """Test failed connection test."""
        mock_result = MagicMock()
        mock_result.status = 'failed'
        mock_run.return_value = mock_result
        
        with pytest.raises(ConnectionException):
            ansible.test_connection('localhost', 'user', 'pass')
    
    def test_write_inventory(self, ansible, tmp_path):
        """Test writing inventory to YAML."""
        inventory_path = tmp_path / "inventory.yml"
        inventory = {'all': {'hosts': {'node1': {'ansible_host': '1.1.1.1'}}}}
        
        ansible._write_inventory(str(inventory_path), inventory)
        
        assert inventory_path.exists()
        with open(inventory_path, 'r') as f:
            content = f.read()
            assert 'node1' in content
            assert '1.1.1.1' in content
