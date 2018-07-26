# -*- coding: utf-8 -*-
import os
import yaml
import socket
import logging

# 如果没有配置过日志，需要配置默认格式，且本段代码要放在所有logger使用前
# 否则logger = logging.getLogger(__name__)写日志会报错
if len(logging.getLogger().handlers) == 0:
    logging.basicConfig(level=logging.DEBUG)

# 设定requests库log级别
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("matplotlib").setLevel(logging.ERROR)


class ConfigLoader(object):
    """读取yaml配置文件"""
    def __init__(self, config_path=None):
        self._config_path = config_path or self._absolute_path('../../conf/config.yaml')
        self._load()
    
    @staticmethod
    def _absolute_path(path):
        return os.path.join(os.path.dirname(__file__), path)

    def _load(self):
        with open(self._config_path, 'r') as f:
            self._conf = yaml.load(f)

    @property
    def conf(self):
        return self._conf

    @property
    def runtime_mode(self):
        """判断运行环境是「开发」还是「生产」"""
        hostname = socket.gethostname()
        return 'prod' if hostname.startswith('ec') or hostname.startswith('vpc') else 'dev'


config = ConfigLoader()
