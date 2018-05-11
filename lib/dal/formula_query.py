# coding: utf-8
import requests
import json
import logging
from collections import Counter
from collections import defaultdict
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# 加载配置
from utils.config_loader import config
conf = config.conf

from dal.dao import question_tag, question_cluster

class FormulaQuery(object):
    def __init__(self):
        # self._question_info = question_dao
        self._logger = logging.getLogger(__name__)
        self._runtime_mode = conf.runtime_mode
        if self._runtime_mode == "prod":
            self.url_api = conf['formula_query_api']['prod_url_api']
        else:
            self.url_api = conf['formula_query_api']['dev_url_api']


    def _get_formula_similarity(self, question_id, size = 40):
        '''
        根据题目ID得到前size个结果
        '''
        #api = 'http://formulasim.uae.shensz.local/lquestion?question_id={0}&num={1}'.format(question_id, size)
        #api = conf['formula_api'] + '?question_id={0}&num={1}'.format(question_id, size)
        api = self.url_api + '?question_id={0}&num={1}'.format(question_id, size)
        resp = requests.get(api)
        resp_dict = json.loads(resp.text)
        result_tag = defaultdict(list)
        # 公式返回结果错误
        if resp_dict['status'] is not True:
            self._logger.error('formula return no result!  Response status: %s', resp_dict['status'])
            raise ValueError(('题目%s不存在'% question_id, ))
        else:
            for question in resp_dict['data']:
                # index = question['index']
                id_ = question['question_id']
                tag_info = question_tag(id_)
                # 统计结果中各个课本下的章节
                if tag_info != [] and tag_info is not None:
                    for book_id, title in tag_info:
                        result_tag[book_id].append(title)
                cluster = question_cluster(id_)
                result_tag['cluster'].append(cluster[0]) if cluster != [] else None
        return result_tag

    def _sort_result_tag(self, result_tag):
        # 如果没有结果, 输出警告
        if result_tag == defaultdict(list):
            self._logger.error('formula return None!')
        # Counter排序
        else:
            sorted_cluster = Counter(result_tag['cluster'])
            if len(sorted_cluster) == 0:
                self._logger.error("sorted_cluster is None!")
            sorted_chapter = defaultdict(dict)
            for book_id, chapter_title in result_tag.iteritems():
                if book_id != 'cluster':
                    sorted_chapter[book_id] = Counter(result_tag[book_id])
        return sorted_chapter, sorted_cluster

    def get_recomment_result(self, question_id, size = 10, topN = 3):
        '''
        公式检索接口
        Args: 
            question_id: 题目ID
            size: 公式检索返回的题目数
        '''
        result_tag = self._get_formula_similarity(question_id, size = size)
        sorted_chapter, sorted_cluster = self._sort_result_tag(result_tag)
        cluster_ranklist = defaultdict(dict)
        cluster_ranklist['cluster']= []
        
        chapter_ranklist = defaultdict(dict)
        chapter_ranklist['chapter'] = defaultdict(list)

        top_cluster = min(topN, len(sorted_cluster))
        for cluster_name, _ in sorted_cluster.most_common(top_cluster):
            cluster_ranklist['cluster'].append(cluster_name)

        for book_id, counter_object in sorted_chapter.iteritems():
            top_chapter = min(topN, len(counter_object))
            for chapter_name, _ in counter_object.most_common(top_chapter):
                chapter_ranklist['chapter'][book_id].append(chapter_name)
        return cluster_ranklist, chapter_ranklist


