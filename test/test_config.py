# coding: utf-8
import os
import sys

from nose.tools import assert_equal
from nose.tools import assert_not_equal

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
from utils.config_loader import ConfigLoader

class TestConfigLoader(object):

    def setup(self):
        self.conf_loader = ConfigLoader()

    def test_config_env(self):
        """环境判断"""
        assert_equal(self.conf_loader.runtime_mode, 'dev')

    def test_config_load(self):
        """配置读取"""
        conf = self.conf_loader.conf
        assert_equal(type(conf), dict)
        assert_equal(type(conf['mysql']), dict)
        assert_equal(type(conf['memcached']), dict)
