# coding: utf-8
import requests
import json
import logging
from collections import Counter
from collections import defaultdict
from collections import namedtuple
import re

from dal.dao.question import *

# 加载配置
from utils.config_loader import config

# 加载运行环境
runtime_mode = config.runtime_mode

class ImageMatching(object):
    """
    图片检索类：
    """
    def __init__(self):
        # self._question_info = question_dao
        self._logger = logging.getLogger(__name__)
        self._url = config.conf['image_query_api']['prod_url_api'] if runtime_mode == 'prod' else config.conf['image_query_api']['dev_url_api']

    def _get_picture_number(self, question_id):
        """
        获取题目的图片数量
        Args:
            question_id: 题目ID
        Returns:
            题目所含图片数量
        """

        # 加载数据列表，元素为 question_id, title, option_a, b, c, d
        question_pictures = question_title_options(question_id)
        # 两个要替换的URL
        for question in question_pictures:
            urls_ = []
            for item in question:
                if item is not None:
                    url_result = re.findall(r'(https?:.*?(jpg|png|wmf|jpeg|gif))', item)
                    if url_result is not None and url_result != []:
                        for i in range(len(url_result)):
                            urls_.append(url_result[i][0])
        return len(urls_)

    def _get_image_similarity(self, question_id, index = 1):
        '''
        根据题目ID得到前若干个结果
        Args:
            question_id: 题目ID
            index: 题目中第几个图片
        Returns:
            result_chapter: defaultdict(book_id: defaultdict(int))
                            {1: defaultdict({title:score, title:score, })}
            result_cluster: defaultdict(int)
                            {cluster_title:score, cluster_title:score }
        '''
        api = self._url + "/q?question_id={0}&index={1}".format(question_id, index)
        resp = requests.get(api)
        resp_dict = json.loads(resp.text)
        # 章节结果
        result_chapter = defaultdict(lambda :defaultdict(int))
        title_to_id = defaultdict(str)
        # 聚类结果
        result_cluster = defaultdict(int)
        cluster_to_id = defaultdict(str)

        # 图像检索返回结果错误
        if resp_dict['status'] is not True:
            self._logger.error('ImageMatching return no result!  Response status: %s', resp_dict['status'])
            raise ValueError(('题目%s  没有图片'% question_id, ))
        else:
            for num, question in enumerate(resp_dict['data']):
                # index = question['index']
                id_ = question['question_id']
                if id_ == question_id: continue
                score = question['score']
                tag_info = question_tag(id_)

                # 统计结果中各个课本下的章节
                if tag_info != [] and tag_info is not None:
                    for book_id, title, chapter_id in tag_info:
                        result_chapter[book_id][title] += score
                        title_to_id[title] = chapter_id

                # 统计结果中聚类
                cluster_list = question_cluster(id_)
                cluster = cluster_list if cluster_list != [] else None
                # print "cluster:   ", cluster
                if cluster != None:
                    result_cluster[cluster[0][0]] += score
                    cluster_to_id[cluster[0][0]] = cluster[0][1]
        return result_chapter, result_cluster, title_to_id, cluster_to_id

    def _sort_result_tag(self, result_chapter, result_cluster, title_to_id, cluster_to_id):
        """
        对得到的聚类与章节标签进行排序，返回排序好的结果
        Args:
            result_chapter: 章节标签
            result_cluster: 聚类标签
        Returns:
            sorted_chapter: 排序好的章节标签(defaultdit(list))
            sorted_cluster: 排序好的聚类标签(defaultdict(list))
        """
        # 如果没有结果, 输出警告
        if len(result_chapter) == 0:
            self._logger.error('ImageMatche return None!')
        # Counter排序
        else:
            # 对聚类排序
            sorted_cluster = []
            cluster_title = sorted(result_cluster.iteritems(), key=lambda d:d[1], reverse=True)
            for i, (title, score) in enumerate(cluster_title):
                sorted_cluster.append({"title":title, "index":i, "id":cluster_to_id[title], "confidence":score})
            if len(sorted_cluster) == 0:
                self._logger.error("sorted_cluster is None!")
            # 对章节排序
            sorted_chapter = defaultdict(list)
            for book_id, chapter_title in result_chapter.iteritems():
                if book_id != 'cluster':
                    tuple_result = sorted(chapter_title.iteritems(), key=lambda d:d[1], reverse=True)
                    for index, (title, score) in enumerate(tuple_result):
                        sorted_chapter[book_id].append({"title":title, "index":index, "id":title_to_id[title], "confidence":score})
        return sorted_chapter, sorted_cluster

    def get_recomment_result(self, question_id, topN = 3):
        '''
        图像检索接口
        Args: 
            question_id: 题目ID
            topN: 公式检索返回的题目数
        '''
        result_chapter, result_cluster, title_to_id, cluster_to_id = self._get_image_similarity(question_id)
        sorted_chapter, sorted_cluster = self._sort_result_tag(result_chapter, result_cluster, title_to_id, cluster_to_id)
        
        cluster_ranklist = defaultdict(dict)
        cluster_ranklist['cluster']= []
        
        chapter_ranklist = defaultdict(dict)
        chapter_ranklist['chapter'] = defaultdict(list)

        top_cluster = min(topN, len(sorted_cluster))
        for i, cluster_name in enumerate(sorted_cluster):
            if i < top_cluster:
                cluster_ranklist['cluster'].append(cluster_name)

        for book_id, counter_object in sorted_chapter.iteritems():
            top_chapter = min(topN, len(counter_object))
            for j, chapter_name in enumerate(counter_object):
                if j < top_chapter:
                    chapter_ranklist['chapter'][book_id].append(chapter_name)
        return cluster_ranklist, chapter_ranklist


