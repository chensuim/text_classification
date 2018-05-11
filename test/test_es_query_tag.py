# coding: utf-8
import os
import sys

from nose.tools import assert_equal
from nose.tools import assert_not_equal

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
from dal.es_query_tag import EsQueryTag
# from utils.config_loader import ConfigLoader

class TestEsQueryTag(object):

    def setup(self):
        self.es = EsQueryTag()

    def test_recommend_many_cluster(self):
        """推荐标签接口"""
        assert_equal(len(self.es.recommend_many_tag("079ad641-6a6d-4061-86f2-e5c66fa80e5a")[1]), 5)
        assert_equal(len(self.es.recommend_many_tag("4b492d6b-81a3-4b5e-9cab-a2dd3f25d54a")[4]), 1)
        assert_equal(len(self.es.recommend_many_tag("4b492d6b-81a3-4b5e-9cab-a2dd3f25d54a")["diff"]), 2)
        assert_equal(len(self.es.recommend_many_tag("4b492d6b-81a3-4b5e-9cab-a2dd3f25d54a")["keypoint"]), 5)
        assert_equal(len(self.es.recommend_many_tag("4b492d6b-81a3-4b5e-9cab-a2dd3f25d54a")["suited"]), 2)


