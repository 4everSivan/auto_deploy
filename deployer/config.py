import os
import yaml

from typing import Dict


class Config:

    def __init__(self, config_file: str) -> None:
        """
        初始化配置对象。

        :param config_file: 配置文件路径
        """
        self.config_file = config_file
        self._effective_config = self._build_effective_configuration()

    def __contains__(self, key: str) -> bool:
        return key in self._effective_config

    def __getitem__(self, key: str) -> str:
        return self._effective_config[key]

    def _build_effective_configuration(self) -> Dict:
        """
        读取 YAML 文件，与默认值进行深度合并，规范化路径并校验日志级别与目录写权限。

        :return: 处理后的有效配置字典
        """

        def __deep_update(base: Dict, overrides: Dict) -> Dict:
            """
            字典深度合并, 将 ``overrides`` 中的值深度合并到 ``base``，对嵌套字典递归处理。

            :param base: 基础字典，将被更新
            :param overrides: 覆盖字典，包含要更新的值
            :return: 深度合并后的字典
            """
            for k, v in overrides.items():
                if isinstance(v, dict) and isinstance(base.get(k), dict):
                    base[k] = __deep_update(dict(base[k]), v)
                else:
                    base[k] = v
            return base

        effective_config = {
            'general': {
                'data_dir': './deploy_data'
            },
            'log': {
                'dir': './deploy_data/log',
                'level': 'INFO'
            }
        }

        with open(self.config_file, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f) or {}
            if not isinstance(loaded, dict):
                raise ValueError('Config YAML must be a mapping at root')

        effective_config = __deep_update(effective_config, loaded)

        general = effective_config.get('general', {})
        log_cfg = effective_config.get('log', {})

        data_dir = os.path.abspath(os.path.expanduser(os.path.expandvars(general.get('data_dir', './deploy_data'))))
        log_dir = os.path.abspath(os.path.expanduser(os.path.expandvars(log_cfg.get('dir', './deploy_data/log'))))

        effective_config['general']['data_dir'] = data_dir
        effective_config['log']['dir'] = log_dir

        level = str(log_cfg.get('level', 'INFO')).upper()
        if level not in {'DEBUG', 'INFO', 'WARNING', 'ERROR'}:
            raise ValueError(f'Invalid log level: {level}')
        effective_config['log']['level'] = level

        for d in [data_dir, log_dir]:
            parent = d if os.path.isdir(d) else os.path.dirname(d) or '.'
            if not os.access(parent, os.W_OK):
                raise PermissionError(f'Directory not writable: {parent}')

        # 检查节点是否配置
        if not effective_config.get('nodes', None):
            raise ValueError('No nodes defined in config file')

        return effective_config


def get_config(config_file: str) -> Config:
    """
    从文件路径创建配置对象并进行基本校验。

    :param config_file: 配置文件路径
    :return: 配置对象实例
    """
    # 检查文件
    if not os.path.exists(config_file):
        raise FileNotFoundError(config_file)
    # 检查读写权限
    if not os.access(config_file, os.R_OK):
        raise PermissionError(f'Config file not readable: {config_file}')
    if not os.access(config_file, os.W_OK):
        raise PermissionError(f'Config file not writeable: {config_file}')

    return Config(config_file)
