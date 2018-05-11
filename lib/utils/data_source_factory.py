# coding: utf-8
import os
import sys
from config_loader import ConfigLoader

class DataSourceFactory(object):
    """
    数据源工厂，获取异构数据来源(MySQL、memcached、Hive...)的客户端
    """
    def __init__(self):
        self._config_loader = ConfigLoader()
        self._conf = self._config_loader.conf
        self._runtime_mode = self._config_loader.runtime_mode

    def _absolute_path(self, path):
        return os.path.join(os.path.dirname(__file__), path)

    def get_mysql_client(self):
        sys.path.append(self._absolute_path('../data/mysql'))
        from mysql import MySQLClient
        mysql_conf = self._conf['mysql'][self._runtime_mode]
        return MySQLClient(mysql_conf)

    def get_mc_client(self):
        sys.path.append(self._absolute_path('../data/mc'))
        from mc import MCClient
        conf = self._conf['memcached'][self._runtime_mode]
        return MCClient(conf['hosts'], default_expire=conf['common_time_expire'])

    def get_hive_client(self):
        sys.path.append(self._absolute_path('../data/hive'))
        from hive_client import HiveClient
        return HiveClient(self._conf['hive'][self._runtime_mode])
