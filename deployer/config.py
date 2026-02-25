import os
import yaml

from typing import Dict, List, Any, cast

from pydantic import ValidationError
from common.utils import expand_path
from common.exceptions import ConfigException
from deployer.models import NodeConfig, SoftwareConfig


class Config:
    """Configuration manager for deployment settings."""
    _effective_config: Dict[str, Any]
    _nodes: List[NodeConfig]

    def __init__(self, config_file: str):
        """
        Initialize configuration.

        Args:
            config_file: Path to YAML configuration file
        """
        self.config_file: str = config_file
        self._nodes: List[NodeConfig] = []
        self._effective_config: Dict[str, Any] = self._build_effective_configuration()
        self._parse_nodes()

    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration."""
        return key in self._effective_config

    def __getitem__(self, key: str) -> Any:
        """Get configuration value by key."""
        return self._effective_config[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default."""
        return self._effective_config.get(key, default)

    def _build_effective_configuration(self) -> Dict[str, Any]:
        """
        Read YAML file and merge with defaults.

        Returns:
            Processed effective configuration dictionary

        Raises:
            ConfigException: If configuration is invalid
        """

        def __deep_update(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
            """
            Deep merge dictionaries.

            Args:
                base: Base dictionary to be updated
                overrides: Override dictionary with new values

            Returns:
                Deeply merged dictionary
            """
            for k, v in overrides.items():
                if isinstance(v, dict) and isinstance(base.get(k), dict):
                    base[k] = __deep_update(dict(base[k]), v)
                else:
                    base[k] = v
            return base

        # Default configuration
        effective_config = {
            'general': {
                'data_dir': './deploy_data',
                'max_concurrent_nodes': 10
            },
            'log': {
                'dir': './deploy_data/log',
                'level': 'INFO'
            }
        }

        # Load YAML file
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded = yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise ConfigException(f'Config file not found: {self.config_file}')
        except yaml.YAMLError as e:
            raise ConfigException(f'Invalid YAML in config file: {e}')

        if not isinstance(loaded, dict):
            raise ConfigException('Config YAML must be a mapping at root')

        # Merge with defaults
        effective_config = __deep_update(effective_config, loaded)
        effective_config = cast(Dict[str, Any], effective_config)

        # Process general settings
        general_cfg = cast(Dict[str, Any], effective_config.get('general', {}))
        log_cfg = cast(Dict[str, Any], effective_config.get('log', {}))

        # Expand paths
        data_dir = expand_path(str(general_cfg.get('data_dir', './deploy_data')))
        log_dir = expand_path(str(log_cfg.get('dir', './deploy_data/log')))

        general_cfg['data_dir'] = data_dir
        log_cfg['dir'] = log_dir
        effective_config['general'] = general_cfg
        effective_config['log'] = log_cfg

        # Validate log level
        level = str(log_cfg.get('level', 'INFO')).upper()
        if level not in {'DEBUG', 'INFO', 'WARNING', 'ERROR'}:
            raise ConfigException(f'Invalid log level: {level}')
        log_cfg['level'] = level

        # Validate max_concurrent_nodes
        max_concurrent = general_cfg.get('max_concurrent_nodes', 10)
        if not isinstance(max_concurrent, int) or max_concurrent < 1:
            raise ConfigException(
                f'max_concurrent_nodes must be a positive integer, got: {max_concurrent}'
            )
        general_cfg['max_concurrent_nodes'] = max_concurrent

        # Check directory write permissions
        for d in [data_dir, log_dir]:
            # If directory exists, check if it's writable
            if os.path.exists(d):
                if not os.access(d, os.W_OK):
                    raise ConfigException(f'Directory not writable: {d}')
            else:
                # If directory doesn't exist, check if parent is writable
                parent = os.path.dirname(d) or '.'
                # Keep going up until we find an existing directory
                while parent and not os.path.exists(parent):
                    parent = os.path.dirname(parent) or '.'
                if parent and not os.access(parent, os.W_OK):
                    raise ConfigException(f'Parent directory not writable: {parent}')

        # Check nodes configuration
        if not effective_config.get('nodes'):
            raise ConfigException('No nodes defined in config file')

        if not isinstance(effective_config['nodes'], list):
            raise ConfigException('nodes must be a list')

        return effective_config

    def _parse_nodes(self) -> None:
        """
        Parse nodes configuration into NodeConfig objects.

        Raises:
            ConfigException: If node configuration is invalid
        """
        nodes_config = cast(List[Dict[str, Any]], self._effective_config.get('nodes', []))

        for node_dict in nodes_config:
            # The node_dict should be a dictionary with a single key (the node name)
            # and its value being the node's configuration.
            # Example: {'node1': {'host': '192.168.1.1'}}
            if not isinstance(node_dict, dict) or len(node_dict) != 1:
                raise ConfigException(f'Invalid node configuration: {node_dict}')

            node_name = list(node_dict.keys())[0]
            node_data = cast(Dict[str, Any], node_dict[node_name])

            if not isinstance(node_data, dict):
                raise ConfigException(f'Node {node_name} configuration must be a dictionary')

            try:
                # Prepare install list
                install_list_raw = cast(List[Dict[str, Any]], node_data.get('install', []))
                install_data: List[SoftwareConfig] = []
                for software_dict_raw in install_list_raw:
                    if not isinstance(software_dict_raw, dict) or len(software_dict_raw) != 1:
                        raise ConfigException(f'Invalid software configuration in node {node_name}')
                    
                    sw_name = list(software_dict_raw.keys())[0]
                    sw_data = cast(Dict[str, Any], software_dict_raw[sw_name])
                    if not isinstance(sw_data, dict):
                        sw_data = {}
                    
                    # Merge defaults
                    sw_pydantic_data = sw_data.copy()
                    sw_pydantic_data['name'] = sw_name
                    
                    try:
                        software_config = SoftwareConfig.model_validate(sw_pydantic_data)
                        install_data.append(software_config)
                    except ValidationError as e:
                        raise ConfigException(f'Software validation error for {sw_name}: {e}')

                # Prepare node data for Pydantic
                node_pydantic_data = {
                    "name": node_name,
                    "host": node_data.get('host', ''),
                    "port": node_data.get('port', 22),
                    "owner_user": node_data.get('owner_user', ''),
                    "owner_pass": node_data.get('owner_pass'),
                    "owner_key": node_data.get('owner_key'),
                    "super_user": node_data.get('super_user', 'root'),
                    "super_pass": node_data.get('super_pass'),
                    "super_key": node_data.get('super_key'),
                    "install": install_data
                }

                # Validate using Pydantic
                node_config = NodeConfig.model_validate(node_pydantic_data)
                self._nodes.append(node_config)

            except ValidationError as e:
                raise ConfigException(f'Validation error for node {node_name}: {e}')
            except Exception as e:
                raise ConfigException(f'Error parsing node {node_name}: {e}')

    def get_nodes(self) -> List[NodeConfig]:
        """Get list of all node configurations."""
        return self._nodes

    def get_node(self, name: str) -> NodeConfig:
        """
        Get node configuration by name.

        Args:
            name: Node name

        Returns:
            NodeConfig object

        Raises:
            ConfigException: If node not found
        """
        for node in self._nodes:
            if node.name == name:
                return node
        raise ConfigException(f'Node not found: {name}')

    def get_max_concurrent_nodes(self) -> int:
        """Get maximum number of concurrent nodes."""
        val = self._effective_config['general']['max_concurrent_nodes']
        return int(val)

    def get_data_dir(self) -> str:
        """Get data directory path."""
        val = self._effective_config['general']['data_dir']
        return str(val)

    def get_log_dir(self) -> str:
        """Get log directory path."""
        val = self._effective_config['log']['dir']
        return str(val)

    def get_log_level(self) -> str:
        """Get log level."""
        val = self._effective_config['log']['level']
        return str(val)


def get_config(config_file: str) -> Config:
    """
    Create configuration object from file path.

    Args:
        config_file: Configuration file path

    Returns:
        Config object instance

    Raises:
        ConfigException: If file doesn't exist or isn't readable
    """
    # Check file exists
    if not os.path.exists(config_file):
        raise ConfigException(f'Config file not found: {config_file}')

    # Check read permission
    if not os.access(config_file, os.R_OK):
        raise ConfigException(f'Config file not readable: {config_file}')

    return Config(config_file)
