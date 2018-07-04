# -*- coding: utf-8 -*-
import requests
import json
from collections import defaultdict
import logging
import sys
import re
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from requests import Session
from dao import question as feed
from lib.utils.config_loader import config

reload(sys)
sys.setdefaultencoding('utf8')

conf = config.conf


class ClusterRecommender(object):
    def __init__(self):
        """
        初始化ES搜索
        """

        # 运行环境
        self._runtime_mode = config.runtime_mode
        # 聚类置信区间
        self.confidence = conf['cluster_confidence']
        # es查询数量
        self._es_query_num = conf['cluster_es_query_num']
        # es查询数量（仅使用keypoint特征时）
        self._es_query_keypoint_num = conf['cluster_es_query_keypoint_num']
        # es查询数量（仅使用chapter特征时）
        self._es_query_chapter_num = conf['cluster_es_query_chapter_num']
        # es查询数量（两个特征都加入时）
        self._es_query_cha_key_num = conf['cluster_es_query_cha_key_num']
        # 聚类TOPN
        self._es_query_topN = conf['es_query_topN']
        # 日志：cluster日志主要保存聚类推荐结果
        self._logger_cluster = logging.getLogger("label_cluster")
        # 获取头文件
        self.headers, self.url_api = self._get_headers()

    def _get_headers(self):
        """
        :return: 文件头，url
        """

        headers = {'content-type': conf['es_query_api']['content-type']}
        url_api = conf['es_query_api']['dev_url_api']
        if self._runtime_mode == "prod":
            url_api = conf['es_query_api']['prod_url_api']

        return headers, url_api

    def _get_es_field(self, question_id):
        """
        :param question_id: 问题ID
        :return: 题目详细信息
        """

        api = self.url_api + '?q=_id:"{0}"&fields=remark,feature'.format(question_id)
        resp = requests.get(api, headers=self.headers, )
        doc = {}
        try:
            data = json.loads(resp.text)['hits']['hits'][0]
        except:
            doc['feature'] = ""
            doc['remark'] = ""
            return doc
        try:
            doc['remark'] = data['fields']['remark'][0]
        except:
            doc['remark'] = ""
        try:
            doc['feature'] = data['fields']['feature'][0]
        except:
            doc['feature'] = ""
        return doc

    def _get_text_similar_bk(self, doc, size=40):
        """
        :param doc: 题目详细信息
        :param size: 匹配的相似题目数量
        :return: 匹配的相似题目详细信息
        """

        body = {"min_score": 0, "explain": False,
                "fields": ["question_id", "cluster_title", "cluster_id"], "from": 0, "size": size,
                "query":
                    {"filtered": {"query":
                        {"more_like_this": {
                            "like": [{"_index": "shensz_jieba_v7", "_type": "solution",
                                      "doc": {"feature": doc['feature'], "remark": doc['remark']}
                                      }],
                            "min_word_len": 2, "min_term_freq": 1
                        }},
                        "filter": {"bool": {"must": [{"nested": {"path": "chapter", "query": {"match_all": {}}}}],
                                            "must_not": []}}}
                    },
                "filter": {}}

        resp_search = requests.post(self.url_api, headers=self.headers, data=json.dumps(body, encoding="utf-8"))
        data = json.loads(resp_search.text, encoding="utf-8")
        return data

    def _get_text_similar(self, version, chapter_id_list, keypoint_id_list, doc):
        size_v0 = self._es_query_num
        size_chapter = self._es_query_chapter_num
        size_keypoint = self._es_query_keypoint_num
        size_cha_key = self._es_query_cha_key_num

        if version == 0:
            body = {"min_score": 0, "explain": False, "fields": ["question_id", "cluster_title", "cluster_id"],
                    "from": 0, "size": size_v0, "query": {"filtered":
                    {
                        "query":
                            {"bool":
                                {"should":
                                    [{
                                        "match":
                                            {
                                                "feature": {"query": doc['feature'],
                                                            "boost": 2
                                                            }
                                            }
                                    },
                                        {
                                            "match":
                                                {
                                                    "remark": {"query": doc['remark']
                                                               }
                                                }
                                        }
                                    ]
                                }
                            },
                        "filter": {"bool": {"must": [{"nested": {"path": "chapter", "query": {"match_all": {}}}}],
                                            "must_not": []}}}
                },
                    "filter": {}}
        # 只有章节
        elif version == 1:
            body = {"min_score": 0, "explain": False, "fields": ["question_id", "cluster_title", "cluster_id"],
                    "from": 0, "size": size_chapter, "query": {"filtered":
                    {
                        "query":
                            {"bool":
                                {"should":
                                    [{
                                        "match":
                                            {
                                                "feature": {"query": doc['feature'],
                                                            "boost": 2
                                                            # ,"boost":10
                                                            }
                                            }
                                    },
                                        {
                                            "match":
                                                {
                                                    "remark": {"query": doc['remark']
                                                               }
                                                }
                                        }
                                    ]
                                    # "min_word_len":2,"min_term_freq":1,
                                }
                            },
                        "filter": {"bool": {"should": [{"nested": {"path": "chapter", "query": {"bool": {"should": [
                            {"terms": {"chapter.id": chapter_id_list}}]}}}}, ], "must_not": []}}}}, "filter": {}}
        # 只有知识点
        elif version == 2:
            body = {"min_score": 0, "explain": False, "fields": ["question_id", "cluster_title", "cluster_id"],
                    "from": 0, "size": size_keypoint, "query": {"filtered":
                    {
                        "query":
                            {"bool":
                                {"should":
                                    [{
                                        "match":
                                            {
                                                "feature": {"query": doc['feature'],
                                                            "boost": 2
                                                            # ,"boost":10
                                                            }
                                            }
                                    },
                                        {
                                            "match":
                                                {
                                                    "remark": {"query": doc['remark']
                                                               }
                                                }
                                        }
                                    ]
                                    # "min_word_len":2,"min_term_freq":1,
                                }
                            },
                        "filter": {"bool": {"should": [{"nested": {"path": "keypoint", "query": {
                            "bool": {"should": [{"terms": {"keypoint.id": keypoint_id_list}}]}}}}, ],
                                            "must_not": []}}}},
                    "filter": {}}
        # 知识点&章节都有
        else:
            body = {"min_score": 0, "explain": False, "fields": ["question_id", "cluster_title", "cluster_id"],
                    "from": 0, "size": size_cha_key, "query": {"filtered":
                    {
                        "query":
                            {"bool":
                                {"should":
                                    [{
                                        "match":
                                            {
                                                "feature": {"query": doc['feature'],
                                                            "boost": 2
                                                            # ,"boost":10
                                                            }
                                            }
                                    },
                                        {
                                            "match":
                                                {
                                                    "remark": {"query": doc['remark']
                                                               }
                                                }
                                        }
                                    ]
                                    # "min_word_len":2,"min_term_freq":1,
                                }
                            },
                        "filter": {"bool": {"must": [{"nested": {"path": "chapter", "query": {
                            "bool": {"should": [{"terms": {"chapter.id": chapter_id_list}}]}}}},
                                                     {"nested": {"path": "keypoint", "query": {
                                                         "bool": {"should": [
                                                             {"terms": {"keypoint.id": keypoint_id_list}}]}}}}],
                                            "must_not": []}}}},
                    "filter": {}}
        resp_search = requests.post(self.url_api, headers=self.headers, data=json.dumps(body, encoding="utf-8"))
        data = json.loads(resp_search.text, encoding="utf-8")
        return data

    @staticmethod
    def _get_cluster_title(question_id, result_dict):
        """
        :param question_id: 题目ID
        :param result_dict: 匹配的相似题目详细信息
        :return: 标签聚类信息
        """
        # 聚类及得分字典
        cluster_title_score = defaultdict(int)
        # 聚类id
        cluster_title_id = {}
        # 对N个结果循环取章节
        for result in result_dict['hits']['hits']:
            if question_id == result['_id']:
                continue
            # 结果的得分
            score = result['_score']
            fields_content = result['fields']
            # 是否有聚类标签
            if fields_content.has_key("cluster_title"):
                cluster = fields_content['cluster_title'][0]
                cluster_title_score[cluster] += score  # 分数累加
                cluster_title_id[cluster] = fields_content['cluster_id'][0]
            # 相似题有章节标签
        return cluster_title_score, cluster_title_id

    def _sort_result_tag(self, cluster_title, cluster_title_id):
        """
        对章节标签，聚类进行汇总
        :param cluster_title: 聚类信息
        :param cluster_title_id: 聚类ID
        :param topN: 返回前N的标签
        :return:
        """
        # 取前TopN道题目作为参考
        topN = self._es_query_topN
        cluster_tag = defaultdict(list)
        # 聚类排序
        sorted_arr = sorted(cluster_title.items(), key=lambda d: d[1], reverse=True)[0:topN]  # 取TOP1
        if len(sorted_arr) > 0:
            for sorted_num, sortedsub in enumerate(sorted_arr):
                cluster_tag['cluster'].append(
                    {"title": sortedsub[0], "index": sorted_num + 1, "confidence": sortedsub[1],
                     "id": str(cluster_title_id[sortedsub[0]])})
        else:
            cluster_tag['cluster'] = []

        return cluster_tag

    def _get_recomment_result(self, version, chapter_id_list, keypoint_id_list, question_id):
        """
        ES检索接口
        Args:
            question_id: 题目ID
            size: ES检索返回的题目数
        """
        doc = self._get_es_field(question_id)
        # 当feature中存在多小问时候，过滤掉该题目
        if u"（1）" in doc['feature'] and u"（2）" in doc['feature']:
            return defaultdict(list)
        result_dict = self._get_text_similar(version, chapter_id_list, keypoint_id_list, doc)
        cluster_title, cluster_title_id = self._get_cluster_title(question_id, result_dict)
        cluster_tag = self._sort_result_tag(cluster_title, cluster_title_id)
        return cluster_tag

    @staticmethod
    def _spider_image(url):
        spider = Session()
        spider.mount("https://", HTTPAdapter(
            max_retries=Retry(total=2, status_forcelist=[500, 502, 503, 504]))
                     )
        res = spider.get(url, timeout=2)
        status_code = res.status_code
        return status_code

    def _question_image_load(self, question_id):
        try:
            # 判断题目是否有图片
            api = self.url_api + '?q=_id:"{0}"&fields=title'.format(question_id)
            resp = requests.get(api, headers=self.headers, )
            try:
                title = json.loads(resp.text)['hits']['hits'][0]['fields']['title'][0]
            except:
                title = ""
            if u"![神算子](http:" not in title:
                return True
            # 获取图片链接
            pattern = re.compile(u"!\[神算子\]\((http.*?)#right\)")
            result_array = pattern.findall(title)
            # 将图片url转换
            # 尝试加载图片
            for url in result_array:
                url = url.replace("http://img.jyeoo.net", "https://image.shensz.cn")
                status_code = self._spider_image(url)
                if str(status_code) == "404":
                    return False
            return True
        except:
            return True

    def recommend_many_cluster(self, question_id):
        """
        用户获取聚类topN结果接口
        Args:
            question_id: 题目ID列表
        Returns:
            list:[cluster_id, cluster_id, ...]
        """

        # 获取搜索题目的章节，知识点
        keypoint_id_list = feed.get_keypoint_from_solution_tag(question_id)
        chapter_id_list = feed.get_chapter_from_solution_tag(question_id)
        if keypoint_id_list != [] and chapter_id_list != []:
            version = 3
        elif chapter_id_list:
            version = 1
        elif keypoint_id_list:
            version = 2
        else:
            version = 0
        cluster_tag = self._get_recomment_result(version, chapter_id_list, keypoint_id_list, question_id)
        cluster_result = []
        if len(cluster_tag['cluster']) >= 1:
            for cluster in cluster_tag['cluster']:
                if cluster['confidence'] < self.confidence: continue
                if len(cluster_result) >= self._es_query_topN: continue
                # 尝试加载图片
                if not self._question_image_load(question_id): continue
                cluster_result.append(cluster["id"])
                self._logger_cluster.info(
                    "recommend question_id to cluster: {'question_id':'%s', 'cluster_id':'%s', 'confidence':%s}"
                    % (question_id, cluster["id"], cluster['confidence']))
        return cluster_result


if __name__ == '__main__':
    es = ClusterRecommender()
    print es.recommend_many_cluster("000b0cae-9398-47fd-a4f1-3a54b55e3651")
