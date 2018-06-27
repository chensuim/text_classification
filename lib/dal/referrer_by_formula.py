# -*- coding: utf-8 -*-
import requests
import json
import logging
from collections import Counter
from collections import defaultdict
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.config_loader import config
from dal.dao.question import question_tag_cluster, question_tag_chapter, \
    question_tag_difficulty, question_tag_suit, question_tag_key_point

reload(sys)
sys.setdefaultencoding('utf-8')


class ReferrerByFormula(object):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
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
        cluster_tag = []
        chapter_tag = defaultdict(list)
        difficulty_tag = []
        suit_tag = []
        key_point_tag = []

        if resp_dict['status'] is not True:
            error_fmt_str = 'ReferrerByFormula query error. Url: {}, question_id: {}, response: {}'
            self._logger.error(error_fmt_str, self._formula_query_url, question_id, resp_dict['status'])
        else:
            for question in resp_dict['data']:
                id_ = question['question_id']

                # cluster tag
                cluster_tag_info = question_tag_cluster(id_)
                cluster_tag = list(cluster_tag_info)

                # chapter tag
                chapter_tag_info = question_tag_chapter(id_)
                for teach_book_id, chapter_title, _ in chapter_tag_info:
                    chapter_tag[teach_book_id].append(chapter_title)

                # difficulty tag
                difficulty_tag_info = question_tag_difficulty(id_)
                difficulty_tag = list(difficulty_tag_info)

                # suit tag
                suit_tag_info = question_tag_suit(id_)
                suit_tag = list(suit_tag_info)

                # key point tag
                key_point_tag_info = question_tag_key_point(id_)
                key_point_tag = list(key_point_tag_info)

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
                    topn_tag = min(topn, len(v))
                    referred_tags[tag_type][k] = [tag_id for tag_id, _ in v.most_common(topn_tag)]
            else:
                topn_tag = min(topn, len(tag_values))
                referred_tags[tag_type] = [tag_id for tag_id, _ in tag_values.most_common(topn_tag)]

        return referred_tags


if __name__ == '__main__':
    referrer = ReferrerByFormula()
    result = referrer.get_referred_result('None')

    print result
