# -*- coding: utf-8 -*-
import os
import sys
from config_loader import ConfigLoader
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'lib'))
from data.mysql.mysql import MySQLClient
from data.mc.mc import MCClient


class DataSourceFactory(object):
    """
    数据源工厂，获取异构数据来源(MySQL、memcached)的客户端
    """
    def __init__(self):
        self._config_loader = ConfigLoader()
        self._conf = self._config_loader.conf
        self._runtime_mode = self._config_loader.runtime_mode

    @staticmethod
    def _absolute_path(path):
        return os.path.join(os.path.dirname(__file__), path)

    def get_mysql_client(self):
        mysql_conf = self._conf['mysql'][self._runtime_mode]
        return MySQLClient(mysql_conf)

    def get_mc_client(self):
        conf = self._conf['memcached'][self._runtime_mode]
        return MCClient(conf['hosts'], default_expire=conf['common_time_expire'])
