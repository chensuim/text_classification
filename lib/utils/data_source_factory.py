# -*- coding: utf-8 -*-
from config_loader import ConfigLoader
from lib.data.mysql.mysql import MySQLClient
from lib.data.mc.mc import MCClient


class DataSourceFactory(object):
    """
    数据源工厂，获取异构数据来源(MySQL、memcached)的客户端
    """
    def __init__(self):
        self._config_loader = ConfigLoader()
        self._conf = self._config_loader.conf
        self._runtime_mode = self._config_loader.runtime_mode

    def get_mysql_client(self):
        mysql_conf = self._conf['mysql'][self._runtime_mode]
        return MySQLClient(mysql_conf)

    def get_mc_client(self):
        conf = self._conf['memcached'][self._runtime_mode]
        return MCClient(conf['hosts'], default_expire=conf['common_time_expire'])
