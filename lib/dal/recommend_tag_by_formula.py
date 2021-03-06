# -*- coding: utf-8 -*-
import requests
import json
import logging
import sys
from collections import Counter
from collections import defaultdict
from lib.utils.config_loader import config
from lib.dal.dao.question import *

reload(sys)
sys.setdefaultencoding('utf-8')


class TagRecommenderByFormula(object):
    def __init__(self):
        self._logger = logging.getLogger('label_tag.formula')
        self._runtime_mode = config.runtime_mode

        if self._runtime_mode == 'prod':
            self._formula_query_url = config.conf['formula_query_api']['prod_url_api']
        else:
            self._formula_query_url = config.conf['formula_query_api']['dev_url_api']

    def _get_tags(self, question_id, query_size=40):
        """
        :param question_id: 检索题目id
        :param query_size: 检索返回结果条目数量
        :return:
        """

        formula_query_api = '{0}?question_id={1}&num={2}'.format(self._formula_query_url, question_id, query_size)
        resp = requests.get(formula_query_api)
        resp_dict = json.loads(resp.text)
        # resp_dict = {
        #     'status': True,
        #     'data': [
        #         {
        #             'question_id': 'ea67af4b-2cd8-4bc2-88d3-8c87abcfb474',
        #             'score': 0.8
        #         }
        #     ]
        # }
        cluster_tag = []
        chapter_tag = defaultdict(list)
        difficulty_tag = []
        suit_tag = []
        key_point_tag = []

        if resp_dict['status'] is not True:
            error_str_fmt = 'ReferrerByFormula query error. Question_id: {}'
            self._logger.error(error_str_fmt.format(question_id))
        else:
            for question in resp_dict['data']:
                _id = question['question_id']
                score = question['score']

                if _id == question_id:
                    continue

                # cluster tag
                cluster_tag_info = question_tag_cluster(_id)
                cluster_tag = [(score, cluster_id) for cluster_id in cluster_tag_info]

                # chapter tag
                chapter_tag_info = question_tag_chapter(_id)
                for teach_book_id, chapter_id in chapter_tag_info:
                    chapter_tag[teach_book_id].append((score, chapter_id))

                # difficulty tag
                difficulty_tag_info = question_tag_difficulty(_id)
                difficulty_tag = [(score, difficulty_id) for difficulty_id in difficulty_tag_info]

                # suit tag
                suit_tag_info = question_tag_suit(_id)
                suit_tag = [(score, suit_id) for suit_id in suit_tag_info]

                # key point tag
                key_point_tag_info = question_tag_key_point(_id)
                key_point_tag = [(score, key_point_id) for key_point_id in key_point_tag_info]

        return {'cluster': cluster_tag,
                'chapter': chapter_tag,
                'difficulty': difficulty_tag,
                'suit': suit_tag,
                'key_point': key_point_tag}

    @staticmethod
    def _sort_tags(tags):
        sorted_tags = {}

        for tag_type, tag_values in tags.iteritems():
            if tag_type == 'chapter':
                sorted_tags[tag_type] = {k: Counter(v) for k, v in tag_values.iteritems()}
            else:
                sorted_tags[tag_type] = Counter(tag_values) if tag_values else {}

        return sorted_tags

    def get_referred_result(self, question_id, query_size=40, topn=3):
        """
        :param question_id: 检索题目id
        :param query_size: 检索返回结果条目数量
        :param topn: 置信度，取前topn个结果
        :return:
        """

        tags = self._get_tags(question_id, query_size)
        sorted_tags = self._sort_tags(tags)
        referred_tags = {}

        for tag_type, tag_values in sorted_tags.iteritems():
            if tag_type == 'chapter':
                referred_tags[tag_type] = {}
                for k, v in tag_values.iteritems():
                    size = min(topn, len(v))
                    referred_tags[tag_type][k] = [tag_id for tag_id, _ in v.most_common(size)] if v else []
            else:
                size = min(topn, len(tag_values))
                referred_tags[tag_type] = [tag_id for tag_id, _ in tag_values.most_common(size)] if tag_values else []

        return referred_tags


if __name__ == '__main__':
    recommender = TagRecommenderByFormula()
    result = recommender.get_referred_result('None')

    print result
