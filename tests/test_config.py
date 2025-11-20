"""
Tests for deployer.config module.
"""

import pytest
import tempfile
import os
from pathlib import Path

from deployer.config import Config, get_config
from deployer.models import NodeConfig, SoftwareConfig
from common.exceptions import ConfigException


class TestConfig:
    """Tests for Config class."""
    
    def test_load_valid_config(self, sample_config_file):
        """Test loading a valid configuration file."""
        config = Config(str(sample_config_file))
        assert config is not None
        assert len(config.get_nodes()) == 2
    
    def test_get_nodes(self, sample_config_file):
        """Test getting all nodes."""
        config = Config(str(sample_config_file))
        nodes = config.get_nodes()
        assert len(nodes) == 2
        assert all(isinstance(node, NodeConfig) for node in nodes)
    
    def test_get_node_by_name(self, sample_config_file):
        """Test getting specific node by name."""
        config = Config(str(sample_config_file))
        node = config.get_node('test_node_01')
        assert node.name == 'test_node_01'
        assert node.host == '192.168.1.100'
        assert node.port == 22
    
    def test_get_nonexistent_node(self, sample_config_file):
        """Test getting non-existent node raises exception."""
        config = Config(str(sample_config_file))
        with pytest.raises(ConfigException, match='Node not found'):
            config.get_node('nonexistent')
    
    def test_get_max_concurrent_nodes(self, sample_config_file):
        """Test getting max concurrent nodes."""
        config = Config(str(sample_config_file))
        assert config.get_max_concurrent_nodes() == 5
    
    def test_get_log_level(self, sample_config_file):
        """Test getting log level."""
        config = Config(str(sample_config_file))
        assert config.get_log_level() == 'DEBUG'
    
    def test_missing_config_file(self):
        """Test loading non-existent config file."""
        with pytest.raises(ConfigException, match='Config file not found'):
            Config('/nonexistent/config.yml')
    
    def test_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML."""
        config_file = tmp_path / 'invalid.yml'
        config_file.write_text('invalid: yaml: content:')
        with pytest.raises(ConfigException, match='Invalid YAML'):
            Config(str(config_file))
    
    def test_missing_nodes(self, tmp_path):
        """Test config without nodes."""
        config_file = tmp_path / 'no_nodes.yml'
        config_file.write_text('general:\n  data_dir: ./test')
        with pytest.raises(ConfigException, match='No nodes defined'):
            Config(str(config_file))
    
    def test_invalid_log_level(self, tmp_path):
        """Test invalid log level."""
        config_file = tmp_path / 'bad_log.yml'
        config_file.write_text('''
general:
  data_dir: ./test
log:
  level: INVALID
nodes:
  - node1:
      host: localhost
      owner_user: test
      owner_pass: test
      super_pass: test
      install:
        - java:
            version: '11'
            install_path: /opt/java
''')
        with pytest.raises(ConfigException, match='Invalid log level'):
            Config(str(config_file))


class TestNodeConfig:
    """Tests for NodeConfig class."""
    
    def test_valid_node_config(self):
        """Test creating valid node configuration."""
        software = SoftwareConfig(
            name='java',
            version='11',
            install_path='/opt/java'
        )
        node = NodeConfig(
            name='test_node',
            host='192.168.1.1',
            port=22,
            owner_user='testuser',
            owner_pass='testpass',
            super_pass='rootpass',
            install=[software]
        )
        assert node.name == 'test_node'
        assert node.host == '192.168.1.1'
        assert node.port == 22
        assert len(node.install) == 1
    
    def test_missing_required_fields(self):
        """Test node config with missing required fields."""
        with pytest.raises(ConfigException, match='Node name is required'):
            NodeConfig(
                name='',
                host='localhost',
                owner_user='test',
                owner_pass='test',
                super_pass='test',
                install=[]
            )
    
    def test_invalid_port(self):
        """Test node config with invalid port."""
        with pytest.raises(ConfigException, match='Invalid port'):
            NodeConfig(
                name='test',
                host='localhost',
                port=99999,
                owner_user='test',
                owner_pass='test',
                super_pass='test',
                install=[SoftwareConfig('java', '11', '/opt/java')]
            )
    
    def test_missing_credentials(self):
        """Test node config without credentials."""
        with pytest.raises(ConfigException, match='owner_pass or owner_key'):
            NodeConfig(
                name='test',
                host='localhost',
                owner_user='test',
                super_pass='test',
                install=[SoftwareConfig('java', '11', '/opt/java')]
            )
    
    def test_get_software_by_name(self):
        """Test getting software by name."""
        java = SoftwareConfig('java', '11', '/opt/java')
        python = SoftwareConfig('python', '3.9', '/opt/python')
        node = NodeConfig(
            name='test',
            host='localhost',
            owner_user='test',
            owner_pass='test',
            super_pass='test',
            install=[java, python]
        )
        assert node.get_software_by_name('java') == java
        assert node.get_software_by_name('python') == python
        assert node.get_software_by_name('nonexistent') is None


class TestSoftwareConfig:
    """Tests for SoftwareConfig class."""
    
    def test_valid_software_config(self):
        """Test creating valid software configuration."""
        software = SoftwareConfig(
            name='java',
            version='11',
            install_path='/opt/java',
            source='url',
            source_path='https://example.com/jdk.tar.gz'
        )
        assert software.name == 'java'
        assert software.version == '11'
        assert software.source == 'url'
    
    def test_missing_required_fields(self):
        """Test software config with missing fields."""
        with pytest.raises(ConfigException, match='Software name is required'):
            SoftwareConfig(name='', version='11', install_path='/opt')
    
    def test_invalid_source(self):
        """Test software config with invalid source."""
        with pytest.raises(ConfigException, match='Invalid source'):
            SoftwareConfig(
                name='java',
                version='11',
                install_path='/opt/java',
                source='invalid'
            )
    
    def test_missing_source_path_for_url(self):
        """Test URL source without source_path."""
        with pytest.raises(ConfigException, match='source_path is required'):
            SoftwareConfig(
                name='java',
                version='11',
                install_path='/opt/java',
                source='url'
            )
    
    def test_path_expansion(self, tmp_path):
        """Test install path expansion."""
        software = SoftwareConfig(
            name='java',
            version='11',
            install_path='~/java'
        )
        assert '~' not in software.install_path
        assert os.path.isabs(software.install_path)


class TestGetConfig:
    """Tests for get_config function."""
    
    def test_get_config_success(self, sample_config_file):
        """Test successful config loading."""
        config = get_config(str(sample_config_file))
        assert isinstance(config, Config)
    
    def test_get_config_file_not_found(self):
        """Test get_config with non-existent file."""
        with pytest.raises(ConfigException, match='not found'):
            get_config('/nonexistent/config.yml')
    
    def test_get_config_not_readable(self, tmp_path):
        """Test get_config with unreadable file."""
        config_file = tmp_path / 'unreadable.yml'
        config_file.write_text('test: data')
        os.chmod(config_file, 0o000)
        try:
            with pytest.raises(ConfigException, match='not readable'):
                get_config(str(config_file))
        finally:
            os.chmod(config_file, 0o644)
