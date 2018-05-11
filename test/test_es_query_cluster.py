# coding: utf-8
import os
import sys

from nose.tools import assert_equal
from nose.tools import assert_not_equal

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
from dal.es_query_cluster import EsQueryCluster
# from utils.config_loader import ConfigLoader

class TestEsQueryCluster(object):

    def setup(self):
        self.es = EsQueryCluster()
        print "聚类推荐测试..."

    def test_recommend_many_cluster(self):
        """推荐接口"""
        assert_equal(len(self.es.recommend_many_cluster("079ad641-6a6d-4061-86f2-e5c66fa80e5a")), 0)
        assert_equal(len(self.es.recommend_many_cluster("000b0cae-9398-47fd-a4f1-3a54b55e3651")), 1)


