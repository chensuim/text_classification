# -*- coding: utf-8 -*-
import sys
import logging.config
from collections import defaultdict
import dao.question as question
import dao.write_info_to_mysql as feed
from es_query_tag import EsQueryTag
from es_query_cluster import EsQueryCluster

reload(sys)
sys.setdefaultencoding('utf8')

_logger = logging.getLogger("root."+__name__)
es = EsQueryTag()
es_cluster = EsQueryCluster()


def label_chapter_zj_for_question(year, questions_to_label_list):
    """
    对浙教版未确定章节的题目标定章节
    """
    values = []
    for question_id, chapter_list in questions_to_label_list.iteritems():
        # 该题目仅有一个推荐候选章节时，才插入
        if len(chapter_list) == 1:
            value = tuple([question_id, 5, chapter_list.pop()])
            values.append(value)
    # 批量化插入mysql
    feed.set_question_chapter(values)
    _logger.info("本次标定章节的题目共： %s 道", len(values))


def label_summary_tags_for_questions(questions_to_label):
    """
    对所有题目进行标定
    :param questions_to_label: 题目列表
    """
    values = defaultdict(list)
    questions_to_label_num = len(questions_to_label)
    _logger.info("length of questions_to_label: %s", questions_to_label_num)
    questions_to_label_index = 0
    for question_id,questions_to_label_value in questions_to_label.iteritems():
        questions_to_label_index += 1
        # _logger.info("finished query %s/%s"%(questions_to_label_index, questions_to_label_num))
        try:
            result_dict = es.recommend_many_tag(question_id)
        except Exception as v:
            _logger.error("ES_QUERY_TAG的锅:%s"%(v))
            continue
        for tag_type, tag_id_list in result_dict.iteritems():
            if tag_type in [1, 2, 3, 4, 5] :
                if "chapter" + str(tag_type) in questions_to_label_value:
                    for chapter_id in tag_id_list:
                        value = tuple([question_id, tag_type, chapter_id])
                        values['chapter'].append(value)
                        break
            elif tag_type == "diff" and "difficulty" in questions_to_label_value:
                for tag_id in tag_id_list:
                    value = tuple([question_id, tag_id])
                    values['diff'].append(value)
                    break
            elif tag_type == "suited" and "suit" in questions_to_label_value:
                for tag_id in tag_id_list:
                    value = tuple([question_id, tag_id])
                    values['suited'].append(value)
            elif tag_type == "keypoint" and "keypoint" in questions_to_label_value:
                for tag_id in tag_id_list:
                    value = tuple([question_id, tag_id])
                    values['keypoint'].append(value)
            else:
                _logger.info("tag_type can not recognised!")
    # 批量化插入mysql
    try:
        feed.set_question_chapter(values['chapter'])
    except:
        _logger.error("feed to chapter error")
    try:
        feed.set_question_keypoints(values['keypoint'])
    except:
        _logger.error("feed to keypoint error")
    try:
        feed.set_question_suit(values['suited'])
    except:
        _logger.error("feed to suited error")
    try:
        feed.set_question_difficulty(values['diff'])
    except:
        _logger.error("feed to diff error")
    _logger.info("本次标定标签的题目共： %s 道",
                 len(values['chapter'])+len(values['keypoint'])+len(values['suited'])+len(values['diff']))


def label_cluster_for_questions(year):
    """
    对未确定聚类的题目进行标定
    """
    if year is None:
        return
    # 还未被标定过的题目
    questions_to_label = question.get_no_labeled_cluster_questions_by_year(year)
    # 被拒绝过机器标定的题目
    questions_denied = question.get_denied_cluster_questions_by_year(year)
    # 题目应该被否定的聚类ID列表
    clusters_id_by_question = defaultdict(list)
    for question_id, _, cluster_id in questions_denied:
        clusters_id_by_question[question_id].append(str(cluster_id))

    values = []
    questions_to_label += questions_denied
    _logger.info("length of questions_to_label: %s", len(questions_to_label))
    questions_have_label = set()
    for question_num, (question_id, auto_increment_id, _)in enumerate(questions_to_label):
        if question_id in questions_have_label:
            continue
        questions_have_label.add(question_id)
        _logger.info("start es_query_cluster for question_id:%s and question_num:%s and year:%s"%
                     (question_id, question_num, year))
        try:
            result_dict = es_cluster.recommend_many_cluster(question_id)
        except Exception as e:
            _logger.error("ES_QUERY_CLUSTER 的锅: %s", e)
            continue
        if not result_dict:
            continue
        for cluster_id in result_dict:
            if cluster_id in clusters_id_by_question[question_id]:
                continue
            value = tuple([question_id, auto_increment_id, cluster_id])
            values.append(value)
            break
    # 批量化插入mysql
    feed.set_question_cluster(values)
    _logger.info("本次标定聚类的题目共： %s 道", len(values))


def label_tags_for_questions_summary(year):
    if year is not None:
        # 获取需要推荐标签的题目
        question_tag_summary = question.get_no_labeled_intersect_tags_questions_summary(year)
        # 分别对题目进行标签推荐
        label_summary_tags_for_questions(question_tag_summary)
    # 开始推荐浙教版的章节
    version = 5 # 浙江版教材 version=5
    # 获取没有浙教版的题目与 其对应的其他教材的章节标签
    question_id_to_label_zj = question.get_no_labeled_chapter_questions_and_tagID_by_year_and_teach_book_id(year, version)
    # 题目--> [已有的章节信息,...]
    question_chapter_dict = defaultdict(list)
    for question_id, chapter_id in question_id_to_label_zj:
        question_chapter_dict[question_id] = chapter_id.split(",")
    # 在表chapter_map获取浙教版章节对应关系
    question_recommend_chapter_list = defaultdict(set)
    # 其他章节与浙教版的章节映射关系表
    chapter_map = question.get_chapter_map()
    for question_id, chapter_list in question_chapter_dict.iteritems():
        for chapter_id_from in chapter_list:
            chapter_id_to = chapter_map.get(chapter_id_from, None)
            if chapter_id_to != None:
                question_recommend_chapter_list[question_id].add(chapter_id_to)
    # 将推荐的章节信息写入数据库
    label_chapter_zj_for_question(year, question_recommend_chapter_list)


if __name__ == '__main__':
    # label_tags_for_questions_summary(2016)
    question_id_to_label_zj = question.get_no_labeled_chapter_questions_and_tagID_by_year_and_teach_book_id(2016, 5)
    question_chapter_dict = defaultdict(list)
    for question_id, chapter_id in question_id_to_label_zj:
        question_chapter_dict[question_id] = chapter_id.split(",")

    question_recommend_chapter_list = defaultdict(set)
    # 其他章节与浙教版的章节映射关系表
    chapter_map = question.get_chapter_map()
    for question_id, chapter_list in question_chapter_dict.iteritems():
        for chapter_id_from in chapter_list:
            chapter_id_to = chapter_map.get(chapter_id_from, None)
            if chapter_id_to != None:
                question_recommend_chapter_list[question_id].add(chapter_id_to)

    print question_recommend_chapter_list