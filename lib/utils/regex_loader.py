# coding: utf-8
import os
import yaml


class RegexLoader(object):
    """读取yaml配置文件"""
    def __init__(self, config_path=None):
        self._config_path = config_path or self._absolute_path('../../conf/regular_expr.yaml')
        self._load()
    
    def _absolute_path(self, path):
        return os.path.join(os.path.dirname(__file__), path)

    def _load(self):
        with open(self._config_path, 'r') as f:
            self._express = yaml.load(f)

    @property
    def express(self):
        return self._express

regular_express = RegexLoader().express
