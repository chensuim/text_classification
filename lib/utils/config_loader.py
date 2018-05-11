# coding: utf-8
import os
import yaml
import socket
import sys
import logging

# 如果没有配置过日志，需要配置默认格式，且本段代码要放在所有logger使用前
# 否则logger = logging.getLogger(__name__)写日志会报错
if len(logging.getLogger().handlers) == 0:
    logging.basicConfig(level=logging.DEBUG)

class ConfigLoader(object):
    """读取yaml配置文件"""
    def __init__(self, config_path=None):
        self._config_path = config_path or self._absolute_path('../../conf/config.yaml')
        self._load()
    
    def _absolute_path(self, path):
        return os.path.join(os.path.dirname(__file__), path)

    def _load(self):
        with open(self._config_path, 'r') as f:
            self._conf = yaml.load(f)

    @property
    def conf(self):
        return self._conf

    def get_default_mc(self):
        sys.path.append(self._absolute_path('../data/mc'))
        from mc import MCClient
        hosts = self.conf['memcached'][self.runtime_mode]['hosts']
        default_expire = self.conf['memcached'][self.runtime_mode]['common_time_expire']
        return MCClient(hosts, default_expire=default_expire)
    
    @property
    def runtime_mode(self):
        """判断运行环境是「开发」还是「生产」"""
        hostname = socket.gethostname()
        return 'prod' if hostname.startswith('ec') or hostname.startswith('vpc') else 'dev'
        # return "dev"

config = ConfigLoader()