# -*- coding: utf-8 -*-
import logging
from lib.utils.data_source_factory import DataSourceFactory

_mc = DataSourceFactory().get_mc_client()
_mysql = DataSourceFactory().get_mysql_client()
# _mysql = DataSourceFactory().get_test_mysql_client()
_logger = logging.getLogger("db_insertion")


def set_question_cluster(question_clusters):
    """
    标定某题的聚类
    Args:
        question_clusters: [(question_id, auto_increment_id, cluster_id),]
    """
    sql = """INSERT IGNORE INTO
            solution_cluster_similar (cluster_id, question_id, question_int_id, level, create_user, status)
            VALUES(%s, %s, %s, %s, %s, %s)
            """
    values = []
    for question_id, auto_increment_id, cluster_id in question_clusters:
        # create_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        create_user = 'ai'
        status = -1
        value = [cluster_id, question_id, auto_increment_id, 0, create_user, status]
        _logger.info("insert data to solution_cluster_similar:%s" % (str(value)))
        values.append(value)
    datas = tuple(tuple(item) for item in values)
    _mysql.executemany(sql, datas)


def set_question_chapter(question_chapters):
    """
    标定某题的章节
    Args:
        question_chapters: [(question_id, book_id, chapter_id),]
    """
    sql = """INSERT IGNORE INTO
            solution_tag (question_id, tag_id, tag_type, tag, teach_book_id, create_user, status)
            VALUES(%s, %s, %s, %s, %s, %s, %s)
            """
    values = []
    for question_id, book_id, chapter_id in question_chapters:
        # create_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        create_user = 'ai'
        status = -1
        value = [question_id, chapter_id, 'H', chapter_id, book_id, create_user, status]
        _logger.info("insert data to solution_tag for chapter:%s" % (str(value)))
        values.append(value)
    datas = tuple(tuple(item) for item in values)
    _mysql.executemany(sql, datas)


def set_question_difficulty(question_difficulty):
    """
    标定某题的难度
    Args:
        question_difficulty: [(question_id, diff_id),]
    """
    sql = """INSERT IGNORE INTO
            solution_tag (question_id, tag_id, tag_type, create_user, status)
            VALUES(%s, %s, %s, %s, %s)
            """
    values = []
    for question_id, diff_id in question_difficulty:
        # create_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        create_user = 'ai'
        status = -1
        value = [question_id, diff_id, 'A', create_user, status]
        _logger.info("insert data to solution_tag for difficulty:%s" % (str(value)))
        values.append(value)
    datas = tuple(tuple(item) for item in values)
    _mysql.executemany(sql, datas)


def set_question_suit(question_suit):
    """
    标定某题的适用情况
    Args:
        question_difficulty: [(question_id, suit_id),]
    """
    sql = """INSERT IGNORE INTO
            solution_tag (question_id, tag_id, tag, tag_type, create_user, status)
            VALUES(%s, %s, %s, %s, %s, %s)
            """
    values = []
    for question_id, suit_id in question_suit:
        # create_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        create_user = 'ai'
        status = -1
        value = [question_id, suit_id, suit_id, 'B', create_user, status]
        _logger.info("insert data to solution_tag for suit:%s" % (str(value)))
        values.append(value)
    datas = tuple(tuple(item) for item in values)
    _mysql.executemany(sql, datas)


def set_question_keypoints(question_keypoints):
    """
    标定某题的知识点
    Args:
        question_difficulty: [(question_id, keypoints_id),]
    """
    sql = """INSERT IGNORE INTO
            solution_tag (question_id, tag_id, tag, tag_type, create_user, status)
            VALUES(%s, %s, %s, %s, %s, %s)
            """
    values = []
    for question_id, keypoint_id in question_keypoints:
        # create_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        create_user = 'ai'
        status = -1
        value = [question_id, keypoint_id, 'G_' + keypoint_id, 'G', create_user, status]
        _logger.info("insert data to solution_tag for keypoint:%s" % (str(value)))
        values.append(value)
    datas = tuple(tuple(item) for item in values)
    _mysql.executemany(sql, datas)


def set_question_sub_keypints(question_sub_keypoints):
    """
    标定某道题目小问的知识点
    Args:
        question_sub_keypoints: [(question_id, tag_no, tag_id_list),]
    """
    sql = """INSERT IGNORE INTO
            solution_tag (question_id, tag_no, tag_id, tag, tag_type, create_user, status)
            VALUES(%s, %s, %s, %s, %s, %s, %s)
            """
    values = []
    for question_id, tag_no, tag_id_list in question_sub_keypoints:
        for tag_id in tag_id_list:
            create_user = 'ai'
            status = -1
            value = [question_id, tag_no, tag_id, 'G_' + tag_id, 'G', create_user, status]
            _logger.info("insert data to solution_tag for keypoint:%s" % (str(value)))
            values.append(value)
    datas = tuple(tuple(item) for item in values)
    _mysql.executemany(sql, datas)


def clear_labeled_no_reviewed_questions():
    """
    清除所有教研还没有判定的题目（机器重新标定题目时提高精度）
    """
    sql_cluster = """DELETE FROM solution_cluster_similar
        WHERE create_user = 'ai' AND status = %s"""
    sql_tag = """DELETE FROM solution_tag
        WHERE create_user = 'ai' AND status = %s"""
    status = -1
    _mysql.execute(sql_cluster, (status, ))
    _mysql.execute(sql_tag, (status, ))
