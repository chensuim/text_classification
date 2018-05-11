# coding: utf-8
import os
import sys
import uuid

from nose.tools import assert_equal
from nose.tools import assert_not_equal

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
from utils.data_source_factory import DataSourceFactory

class TestDataSourceFactory(object):

    def setup(self):
        self._data_source_factory = DataSourceFactory()

    def test_mysql_client(self):
        """MySQL客户端"""
        mysql_client = self._data_source_factory.get_mysql_client()
        users = mysql_client.all("SELECT username FROM users LIMIT 5")
        assert_equal(len(users), 5)

    def test_mc_client(self):
        """memcached客户端"""
        mc_client = self._data_source_factory.get_mc_client()
        random_val = str(uuid.uuid4())
        mc_client.set('test_key', random_val, time_expire=10)
        val_from_cache = mc_client.get('test_key')
        assert_equal(val_from_cache, random_val)

