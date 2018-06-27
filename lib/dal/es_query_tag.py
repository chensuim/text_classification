# -*- coding: utf-8 -*-
import requests
import json
from collections import defaultdict
import logging
import time
import sys
import collections
from lib.utils.config_loader import config

reload(sys)
sys.setdefaultencoding('utf8')

conf = config.conf


class EsQueryTag(object):
    def __init__(self):
        '''
        初始化ES搜索
        '''
        # 运行环境
        self._runtime_mode = config.runtime_mode
        # 章节置信区间
        self.chapter_confidence = conf['chapter_confidence']
        # 难度置信区间
        self.diff_confidence = conf['diff_confidence']
        # 适应情况置信区间
        self.suited_confidence = conf['suited_confidence']
        # 知识点置信区间
        self.keypoint_confidence = conf['keypoint_confidence']
        # es章节查询数量
        self._chapter_es_query_num = conf['chapter_es_query_num']
        # es难度查询数量
        self._diff_es_query_num = conf['diff_es_query_num']
        # es适应情况查询数量
        self._suited_es_query_num = conf['suited_es_query_num']
        # es知识点查询数量
        self._keypoint_es_query_num = conf['keypoint_es_query_num']
        # 最大查询数量
        self._max_es_query_num = max([self._chapter_es_query_num, self._diff_es_query_num,
                                      self._suited_es_query_num, self._keypoint_es_query_num])
        # 标签TOPN
        self._es_query_topN = conf['es_query_topN']
        # 日志：tag日志主要保存推荐结果
        self._logger = logging.getLogger("root."+__name__)
        self._logger_tag = logging.getLogger("tag")
        # 获取文件头
        self.headers, self.url_api = self._get_headers()

    def _get_headers(self):
        '''
        :return: 文件头，url
        '''
        headers = {'content-type': conf['es_query_api']['content-type']}
        url_api = conf['es_query_api']['dev_url_api']
        if self._runtime_mode == "prod":
            headers['Cookie'] = conf['es_query_api']['Cookie']
            url_api = conf['es_query_api']['prod_url_api']

        return headers, url_api

    def _get_es_field(self, question_id):
        '''
        :param question_id: 问题ID
        :return: 题目详细信息
        '''
        api = self.url_api + '?q=_id:"{0}"&fields=remark,feature,method,analysis'.format(question_id)
        resp = requests.get(api, headers=self.headers, )
        doc = {}
        try:
            data = json.loads(resp.text)['hits']['hits'][0]
        except:
            doc['feature'] = ""
            doc['remark'] = ""
            doc['method'] = ""
            doc['analysis'] = ""
            return doc
        try:
            doc['remark'] = data['fields']['remark'][0]
        except:
            doc['remark'] = ""
        try:
            doc['method'] = data['fields']['method'][0]
        except:
            doc['method'] = ""
        try:
            doc['analysis'] = data['fields']['analysis'][0]
        except:
            doc['analysis'] = ""
        try:
            doc['feature'] = data['fields']['feature'][0]
        except:
            doc['feature'] = ""
        return doc

    def _get_text_similar(self, doc, size):
        '''
        :param doc: 题目详细信息
        :param size: 匹配的相似题目数量
        :return: 匹配的相似题目详细信息
        '''
        body = {"min_score": 0, "explain": False,
                "fields": ["question_id", "chapter.title", "chapter.id",
                           "chapter.teach_book_id", "difficulty", "suited", "keypoint.id"], "from": 0, "size": size,
                "query":
                    {"filtered": {"query":
                        {"more_like_this": {
                            "like": [{"_index": "shensz_jieba_v7", "_type": "solution",
                                      "doc": {"feature": doc['feature'], "remark": doc['remark'],
                                              "method": doc['method'], "analysis": doc['analysis']}
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

    def _get_tag(self, question_id, result_dict):
        '''
        :param question_id: 题目ID
        :param result_dict: 匹配的相似题目详细信息
        :return: 标签聚类信息
        '''
        # 章节及得分字典
        chapter_title = defaultdict(lambda: defaultdict(int))
        diff_dict = defaultdict(int)
        suit_dict = defaultdict(int)
        keypoint_dict = defaultdict(int)
        # 对N个结果循环取章节
        for result_num, result in enumerate(result_dict['hits']['hits']):
            if question_id == result['_id']:
                continue
            # 结果的得分
            score = result['_score']
            fields_content = result['fields']
            # 相似题有章节标签
            if fields_content.has_key('chapter.id') and len(fields_content['chapter.id']) > 0 \
                    and result_num < self._chapter_es_query_num:
                for i, chapter_id in enumerate(fields_content['chapter.id']):
                    chapter_title[chapter_id]['score'] += score
                    chapter_title[chapter_id]['chapter_id'] = chapter_id
                    chapter_title[chapter_id]['title'] = fields_content['chapter.title'][i]
                    chapter_title[chapter_id]['teach_book_id'] = fields_content['chapter.teach_book_id'][i]
            # 相似题有难度标签
            if fields_content.has_key('difficulty') and len(fields_content['difficulty']) > 0 \
                    and result_num < self._diff_es_query_num:
                diff = fields_content['difficulty'][0]
                diff_dict[diff] += score
            # 相似题有适应情况标签
            if fields_content.has_key('suited') and len(fields_content['suited']) > 0 \
                    and result_num < self._suited_es_query_num:
                for suit in fields_content['suited']:
                    suit_dict[suit] += score
            # 相似题有知识点标签
            if fields_content.has_key('keypoint.id') and len(fields_content['keypoint.id']) > 0 \
                    and result_num < self._keypoint_es_query_num:
                for keypoint in fields_content['keypoint.id']:
                    keypoint_dict[keypoint] += score
        return chapter_title, diff_dict, suit_dict, keypoint_dict

    def _sort_result_tag(self, chapter_title, diff_dict, suit_dict, keypoint_dict, topN):
        '''
        对章节标签，聚类进行汇总
        :param chapter_title: 章节信息
        :param topN: 返回前N的标签
        :return:
        '''
        # 章节tag
        tag_result_dict = {}
        tag_result_dict["chapter"] = defaultdict(list)
        tag_result_dict["diff"] = []
        tag_result_dict["suited"] = []
        tag_result_dict["keypoint"] = []
        # 章节排序
        chapter_arr = chapter_title.values()
        # 按分数降序排列
        chapter_arr.sort(lambda x, y: 1 if y['score'] - x['score'] > 0 else -1)
        for content in chapter_arr:
            book_id = content['teach_book_id']
            if len(tag_result_dict["chapter"][book_id]) >= topN: break
            tag_result_dict["chapter"][book_id].append(
                {"title": content['title'], "confidence": content['score'], "id": content['chapter_id'],
                 'index': len(tag_result_dict["chapter"][book_id]) + 1})
        # 难度排序
        diff_sort_dict = sorted(diff_dict.items(), key=lambda d: d[1], reverse=True)
        for sort_list in diff_sort_dict:
            if len(tag_result_dict["diff"]) >= topN: break
            tag_result_dict["diff"].append(
                {"diff": sort_list[0], "confidence": sort_list[1], 'index': len(tag_result_dict["diff"]) + 1})
        # 适应情况
        suited_sort_dict = sorted(suit_dict.items(), key=lambda d: d[1], reverse=True)
        for suited_list in suited_sort_dict:
            if len(tag_result_dict["suited"]) >= topN: break
            tag_result_dict["suited"].append(
                {"suited": suited_list[0], "confidence": suited_list[1], 'index': len(tag_result_dict["suited"]) + 1})
        # 知识点
        keypoint_sort_dict = sorted(keypoint_dict.items(), key=lambda d: d[1], reverse=True)
        for keypoint_list in keypoint_sort_dict:
            if len(tag_result_dict["keypoint"]) >= topN: break
            tag_result_dict["keypoint"].append(
                {"keypoint": keypoint_list[0], "confidence": keypoint_list[1],
                 'index': len(tag_result_dict["keypoint"]) + 1})
        return tag_result_dict

    def _get_recomment_result(self, question_id, size, topN):
        '''
        ES检索接口
        Args:
            question_id: 题目ID
            size: ES检索返回的题目数
        '''
        # self._logger.info('get_recommend_result: 进入ES检索接口....')
        start_time = time.time()
        doc = self._get_es_field(question_id)
        result_dict = self._get_text_similar(doc, size)
        chapter_title, diff_dict, suit_dict, keypoint_dict = self._get_tag(question_id, result_dict)
        tag_result_dict = self._sort_result_tag(chapter_title, diff_dict, suit_dict, keypoint_dict, topN)
        # self._logger.info("get_recommend_result: ES检索耗时 ->%.2f ms", (time.time() - start_time) * 1000)
        return tag_result_dict

    def recommend_many_tag(self, question_id):
        """
        用户获取聚类topN结果接口
        Args:
            question_id: 题目ID列表
        Returns:
            dict:{book_id:[chapter_id, chapter_id, ...],"diff":[...], "suited":[...], "keypoint":[...]}
        """
        tag_result_dict = self._get_recomment_result(question_id, self._max_es_query_num, self._max_es_query_num)
        tag_result = collections.defaultdict(list)
        # 处理章节信息，包括置信区间，TOPN
        if len(tag_result_dict['chapter']) >= 1:
            for book, chapter_list in tag_result_dict['chapter'].items():
                for chapter in chapter_list:
                    if chapter['confidence'] < self.chapter_confidence: break
                    if len(tag_result[book]) >= self._es_query_topN: break
                    tag_result[book].append(chapter['id'])
                    self._logger_tag.info(
                        "recommend question_id to book: {'question_id':'%s', 'book':'%s', 'id':'%s', 'confidence':%s}"
                        % (question_id, book, chapter['id'], chapter['confidence']))
        # 处理难度信息，包括置信区间，TOPN
        if len(tag_result_dict['diff']) >= 1:
            for diff in tag_result_dict['diff']:
                if diff['confidence'] < self.diff_confidence: break
                if len(tag_result['diff']) >= self._es_query_topN: break
                tag_result['diff'].append(diff['diff'])
                self._logger_tag.info(
                    "recommend question_id to diff: {'question_id':'%s', 'diff':'%s', 'confidence':%s}"
                    % (question_id, diff['diff'], diff['confidence']))
        # 处理适应情况信息，包括置信区间，TOPN
        if len(tag_result_dict['suited']) >= 1:
            for suited in tag_result_dict['suited']:
                if suited['confidence'] < self.suited_confidence: break
                if len(tag_result['suited']) >= self._es_query_topN: break
                tag_result['suited'].append(suited['suited'])
                self._logger_tag.info(
                    "recommend question_id to suited: {'question_id':'%s', 'suited':'%s', 'confidence':%s}"
                    % (question_id, suited['suited'], suited['confidence']))
        # 处理知识点信息，包括置信区间，TOPN
        if len(tag_result_dict['keypoint']) >= 1:
            for keypoint_num, keypoint in enumerate(tag_result_dict['keypoint']):
                # 知识点最多推7个
                if keypoint_num in (1, 2) and keypoint['confidence'] < self.keypoint_confidence: continue
                elif keypoint_num in (3, 4) and keypoint['confidence'] < self.keypoint_confidence * 1.5: continue
                elif keypoint_num in (5, 6) and keypoint['confidence'] < self.keypoint_confidence * 2: continue
                elif keypoint_num >= 7: break
                tag_result['keypoint'].append(keypoint['keypoint'])
                self._logger_tag.info(
                    "recommend question_id to keypoint: {'question_id':'%s', 'keypoint':'%s', 'confidence':%s}"
                    % (question_id, keypoint['keypoint'], keypoint['confidence']))
        return tag_result


if __name__ == "__main__":
    es = EsQueryTag()
    print es.recommend_many_tag("0010c427-a3dd-4c4c-bfe1-9dacae88a3ab")
