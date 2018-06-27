# -*- coding: utf-8 -*-
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))
from utils.auto_mc import *
from utils.data_source_factory import DataSourceFactory

_mc = config.get_default_mc()
_mysql = DataSourceFactory().get_mysql_client()


def get_chapter_map():
    """
    获取浙教版章节 <--> 以及对应的（其他教材的）章节标签
    """
    sql = '''SELECT chapter_to, chapter_from
            FROM chapter_map
            WHERE chapter_from_path LIKE "%%浙教%%" AND status = 1 '''
    result = _mysql.all(sql, ())
    chapter_to_chapter = {}
    for chapter_to, chapter_from in result:
        chapter_to_chapter[chapter_to] = chapter_from
    return chapter_to_chapter


def get_no_labeled_chapter_questions_and_tagID_by_year_and_teach_book_id(year, version):
    """
    获取浙教版未被标注过章节的题目,以及它对应的（其他教材的）章节标签
    Args:
        year: 题目来源年份
        version: 第几套教材...1,2,3
    Returns:
        list: [题目ID,]
    """
    if year is None:
        sql = """SELECT ss.question_id, group_concat(st.tag_id)
                        FROM solution AS ss
                        JOIN solution_tag AS st
                        ON ss.question_id = st.question_id
                        WHERE ss.question_id NOT IN (
                        SELECT question_id FROM solution_tag WHERE tag_type = "H" AND teach_book_id = %s)
                        AND st.tag_type = "H" AND st.status = 1
                        AND ss.source_year is null AND ss.question_id IS NOT NULL AND ss.status != -1 GROUP BY ss.question_id
                        """
        result = _mysql.all(sql, (str(version)))
        return result
    sql = """SELECT ss.question_id, group_concat(st.tag_id)
                FROM solution AS ss
                JOIN solution_tag AS st
                ON ss.question_id = st.question_id
                WHERE ss.question_id NOT IN (
                SELECT question_id FROM solution_tag WHERE tag_type = "H" AND teach_book_id = %s)
                AND st.tag_type = "H" AND st.status = 1
                AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 GROUP BY ss.question_id
                """
    result = _mysql.all(sql, (version, year))
    return result


@auto_mc
def question_title_options(question_id):
    """
    获取所有题目与选项
    Args:
        question_id
    Returns:
        一个数组：数组内元素为[question_id, title, option_a, option_b...]
    """
    sql = '''SELECT title, option_a, option_b, option_c, option_d,
             FROM solution
             WHERE question_id = %s'''
    # result = self._mysql.all(sql)
    result = _mysql.all(sql, (question_id, ))
    return result


@auto_mc
def question_tag_key_point(question_id):
    """
    获取题目的知识点
    Args:
        question_id: 题目ID
    Returns:
        元组: (知识点标签)
    """
    sql = '''SELECT tag_id
             FROM solution_tag
             WHERE tag_type = "G"
             AND status != 0
             AND question_id = %s'''
    result = _mysql.all(sql, (question_id, ))
    return result


@auto_mc
def question_tag_suit(question_id):
    """
    获取题目的适应情况
    Args:
        question_id: 题目ID
    Returns:
        元组: (适应情况标签)
    """
    sql = '''SELECT tag_id
             FROM solution_tag
             WHERE tag_type = "B"
             AND status != 0
             AND question_id = %s'''
    result = _mysql.all(sql, (question_id, ))
    return result


@auto_mc
def question_tag_difficulty(question_id):
    """
    获取题目的难度
    Args:
        question_id: 题目ID
    Returns:
        元组: (难度标签)
    """
    sql = '''SELECT tag_id
             FROM solution_tag
             WHERE tag_type = "A"
             AND status != 0
             AND question_id = %s'''
    result = _mysql.all(sql, (question_id, ))
    return result


@auto_mc
def question_tag_chapter(question_id):
    """
    获取题目的章节
    Args:
        question_id: 题目ID
    Returns:
        元组: (教材版本号，章节名称，章节ID)
    """
    sql = '''SELECT st.teach_book_id, cn.title, cn.id
             FROM solution_tag AS st
             JOIN chapter_new  AS cn
             ON st.tag_id = cn.id
             AND st.question_id = %s
             AND st.tag_type = "H" AND st.status != 0'''
    result = _mysql.all(sql, (question_id, ))
    return result


@auto_mc
def question_tag_cluster(question_id):
    """
    获取题目的聚类
    Args:
        question_id: 题目ID
    Returns:
        元组: (聚类名称)
    """
    sql = '''SELECT sc.title
             FROM solution_cluster AS sc
             JOIN solution_cluster_similar   AS scs
             ON   sc.id = scs.cluster_id
             AND  scs.question_id = %s'''
    result = _mysql.all(sql, (question_id, ))
    return result


@auto_mc
def get_chapter_by_chapter(chapter_id):
    """
    根据已知章节找到浙教新版的教材章节
    Args:
        chapter_id: 章节ID
    Returns:
    """
    sql = '''SELECT chapter_from
            FROM chapter_map
            WHERE chapter_to = %s AND status != 0
            AND chapter_from_path LIKE "%%浙教%%" '''
    result = _mysql.all(sql, (chapter_id, ))
    return result


def get_no_labeled_cluster_questions_by_year(year):
    """
    获取某年未标定聚类的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [[题目ID, 题目自增ID],]
    """
    sql = '''SELECT distinct ss.question_id, ss.auto_increment_id,null
            FROM solution AS ss
            WHERE ss.question_id NOT IN
            (SELECT distinct scs.question_id FROM solution_cluster_similar AS scs)
            AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.auto_increment_id ASC
            '''
    result = _mysql.all(sql, (year, ))
    return result


def get_denied_cluster_questions_by_year(year):
    """
    获取被教研拒绝过聚类的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [[question_id, auto_increment_id, cluster_id]]
    """
    sql = '''SELECT distinct ss.question_id, ss.auto_increment_id, scs.cluster_id
            FROM solution AS ss
            INNER JOIN solution_cluster_similar AS scs
            ON ss.question_id = scs.question_id
            WHERE scs.status = 0
            AND ss.question_id NOT IN
            (SELECT distinct scs_.question_id FROM solution_cluster_similar AS scs_ WHERE scs_.status in (1, -1))
            AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.auto_increment_id ASC
            '''
    result = _mysql.all(sql, (year, ))
    return result


def get_denied_cluster_id_by_question_id(question_id):
    """
    获取题目曾经推荐的聚类
    Args:
        question_id: 题目ID
    Returns:
        list: [cluster_id,cluster_id...]
    """
    sql = '''SELECT distinct cluster_id
            FROM solution_cluster_similar
            WHERE question_id = %s AND status = 0'''
    result = _mysql.all(sql, (question_id, ))
    return result


def get_no_labeled_chapter_questions_by_year(year):
    """
    获取未被标注过章节的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [题目ID,]
    """
    sql = """SELECT ss.question_id
            FROM solution AS ss
            WHERE ss.question_id NOT IN (
            SELECT question_id FROM solution_tag WHERE tag_type = "H")
            AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.question_id ASC;
            """
    result = _mysql.all(sql, (year, ))
    return result


def get_no_labeled_chapter_questions_by_year_and_teach_book_id(year, version):
    """
    获取未被标注过章节的题目
    Args:
        year: 题目来源年份
        version: 第几套教材...1,2,3
    Returns:
        list: [题目ID,]
    """
    sql = """SELECT ss.question_id
                FROM solution AS ss
                WHERE ss.question_id NOT IN (
                SELECT question_id FROM solution_tag WHERE tag_type = "H" AND teach_book_id = %s)
                AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.question_id ASC;
                """
    result = _mysql.all(sql, (version, year))
    return result


def get_no_labeled_chapter_questions_by_year_and_teach_book_id_1(year):
    """
    获取未被标注过教材1章节的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [题目ID,]
    """
    sql = """SELECT ss.question_id
                FROM solution AS ss
                WHERE ss.question_id NOT IN (
                SELECT question_id FROM solution_tag WHERE tag_type = "H" AND teach_book_id = 1)
                AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.question_id ASC;
                """
    result = _mysql.all(sql, (year,))
    return result


def get_no_labeled_chapter_questions_by_year_and_teach_book_id_2(year):
    """
    获取未被标注过教材2章节的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [题目ID,]
    """
    sql = """SELECT ss.question_id
                FROM solution AS ss
                WHERE ss.question_id NOT IN (
                SELECT question_id FROM solution_tag WHERE tag_type = "H" AND teach_book_id = 2)
                AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.question_id ASC;
                """
    result = _mysql.all(sql, (year,))
    return result


def get_no_labeled_chapter_questions_by_year_and_teach_book_id_3(year):
    """
    获取未被标注过教材3章节的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [题目ID,]
    """
    sql = """SELECT ss.question_id
                FROM solution AS ss
                WHERE ss.question_id NOT IN (
                SELECT question_id FROM solution_tag WHERE tag_type = "H" AND teach_book_id = 3)
                AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.question_id ASC;
                """
    result = _mysql.all(sql, (year,))
    return result


def get_no_labeled_chapter_questions_by_year_and_teach_book_id_4(year):
    """
    获取未被标注过教材4章节的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [题目ID,]
    """
    sql = """SELECT ss.question_id
                FROM solution AS ss
                WHERE ss.question_id NOT IN (
                SELECT question_id FROM solution_tag WHERE tag_type = "H" AND teach_book_id = 4)
                AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.question_id ASC;
                """
    result = _mysql.all(sql, (year,))
    return result


def get_no_labeled_chapter_questions_by_year_and_teach_book_id_5(year):
    """
    获取未被标注过教材5章节的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [题目ID,]
    """
    sql = """SELECT ss.question_id
                FROM solution AS ss
                WHERE ss.question_id NOT IN (
                SELECT question_id FROM solution_tag WHERE tag_type = "H" AND teach_book_id = 5)
                AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.question_id ASC;
                """
    result = _mysql.all(sql, (year,))
    return result


def get_denied_chapter_questions_by_year(year):
    """
    获取被教研拒绝过章节的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [[question_id, cluster_id]]
    """
    sql = """SELECT ss.question_id, st.tag_id, st.teach_book_id
            FROM solution AS ss
            INNER JOIN solution_tag AS st
            ON ss.question_id = st.question_id
            WHERE st.status = 0 AND st.tag_type = 'H'
            AND ss.question_id NOT IN
            (SELECT question_id FROM solution_tag WHERE STATUS IN (1, -1) and tag_type = 'H')
            AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.auto_increment_id ASC
            """
    result = _mysql.all(sql, (year, ))
    return result


def get_no_labeled_difficulty_questions_by_year(year):
    """
    获取未被标注过难度的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [题目ID,]
    """
    sql = """SELECT ss.question_id
            FROM solution AS ss
            WHERE ss.question_id NOT IN (
            SELECT question_id FROM solution_tag WHERE tag_type = "A")
            AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.question_id ASC
            """
    result = _mysql.all(sql, (year, ))
    return result


def get_denied_difficulty_questions_by_year(year):
    """
    获取被教研拒绝过难度的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [[question_id, tag_id]]
    """
    sql = """SELECT ss.question_id, st.tag_id
            FROM solution AS ss
            INNER JOIN solution_tag AS st
            ON ss.question_id = st.question_id
            WHERE st.status = 0 AND st.tag_type = 'A'
            AND ss.question_id NOT IN
            (SELECT question_id FROM solution_tag WHERE STATUS IN (1, -1) AND tag_type = "A")
            AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.auto_increment_id ASC
            """
    result = _mysql.all(sql, (year, ))
    return result


def get_no_labeled_suit_questions(year):
    """
    获取未被标注过适应情况的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [题目ID,]
    """
    sql = """SELECT ss.question_id
            FROM solution AS ss
            WHERE ss.question_id NOT IN (
            SELECT question_id FROM solution_tag WHERE tag_type = "B")
            AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.question_id ASC
            """
    result = _mysql.all(sql, (year, ))
    return result


def get_denied_suit_questions(year):
    """
    获取被教研拒绝过适应情况的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [[question_id, tag_id]]
    """
    sql = """SELECT ss.question_id, st.tag_id
            FROM solution AS ss
            INNER JOIN solution_tag AS st
            ON ss.question_id = st.question_id
            WHERE st.status = 0 AND st.tag_type = 'B'
            AND ss.question_id NOT IN
            (SELECT question_id FROM solution_tag WHERE STATUS IN (1, -1) AND tag_type = "B")
            AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.auto_increment_id ASC
            """
    result = _mysql.all(sql, (year, ))
    return result


def get_no_labeled_keypoints_questions(year):
    """
    获取未被标注过知识点的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [题目ID,]
    """
    sql = """SELECT ss.question_id
            FROM solution AS ss
            WHERE ss.question_id NOT IN (
            SELECT question_id FROM solution_tag WHERE tag_type = "G" AND status = 1 AND tag_no = 0)
            AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.question_id ASC
            """
    result = _mysql.all(sql, (year, ))
    return result


def get_denied_keypoints_questions(year):
    """
    获取被教研拒绝过知识点的题目
    Args:
        year: 题目来源年份
    Returns:
        list: [[question_id, tag_id]]
    """
    sql = """SELECT ss.question_id, st.tag_id
            FROM solution AS ss
            INNER JOIN solution_tag AS st
            ON ss.question_id = st.question_id
            WHERE st.status = 0 AND st.tag_type = 'G'
            AND ss.question_id NOT IN
            (SELECT question_id FROM solution_tag WHERE STATUS IN (1, -1) AND tag_type = "G")
            AND ss.source_year = %s AND ss.question_id IS NOT NULL AND ss.status != -1 ORDER BY ss.auto_increment_id ASC
            """
    result = _mysql.all(sql, (year, ))
    return result


def get_no_labeled_intersect_tags_questions(year):
    questions_chapter = set(get_no_labeled_chapter_questions_by_year(year))
    questions_difficulty = set(get_no_labeled_difficulty_questions_by_year(year))
    questions_suit = set(get_no_labeled_suit_questions(year))
    questions_keypoint = set(get_no_labeled_keypoints_questions(year))

    intersect_questions_tag = questions_chapter & questions_difficulty & questions_suit & questions_keypoint
    return intersect_questions_tag, questions_chapter, questions_difficulty, questions_suit, questions_keypoint


def reduce_tag(x, y):
    for key, value in x.items():
        if y.has_key(key):
            y[key] = value + y[key]
        else:
            y[key] = value
    return y


def get_no_labeled_intersect_tags_questions_summary(year):
    """
    :param year: 待推荐年份
    :return: {'question_id':[chapter1,],}
    """
    questions_chapter_list = []
    for version in range(1, 6):
        questions_chapter_list.append(dict.fromkeys(get_no_labeled_chapter_questions_by_year_and_teach_book_id(year, version),
                ["chapter{}".format(version)]))
    """
    questions_chapter_1 = dict.fromkeys(get_no_labeled_chapter_questions_by_year_and_teach_book_id_1(year),
                                        ["chapter1"])
    questions_chapter_2 = dict.fromkeys(get_no_labeled_chapter_questions_by_year_and_teach_book_id_2(year),
                                        ["chapter2"])
    questions_chapter_3 = dict.fromkeys(get_no_labeled_chapter_questions_by_year_and_teach_book_id_3(year),
                                        ["chapter3"])
    questions_chapter_4 = dict.fromkeys(get_no_labeled_chapter_questions_by_year_and_teach_book_id_4(year),
                                        ["chapter4"])
    questions_chapter_5 = dict.fromkeys(get_no_labeled_chapter_questions_by_year_and_teach_book_id_5(year),
                                        ["chapter5"])
    """
    questions_difficulty = dict.fromkeys(get_no_labeled_difficulty_questions_by_year(year), ["difficulty"])
    questions_suit = dict.fromkeys(get_no_labeled_suit_questions(year), ["suit"])
    questions_keypoint = dict.fromkeys(get_no_labeled_keypoints_questions(year), ["keypoint"])

    question_tag_summary = reduce(reduce_tag, [questions_chapter_list[0], questions_chapter_list[1], questions_chapter_list[2],
                                               questions_chapter_list[3], questions_chapter_list[4],
                                               questions_difficulty, questions_suit, questions_keypoint])
    return question_tag_summary


def get_chapter_from_solution_tag(question_id):
    """
    获取题目的章节标签来预测聚类
    :param question_id:
    :return:
    """
    sql = """
          SELECT tag_id FROM solution_tag
          WHERE question_id = %s AND tag_type = "H"
          AND status = 1
          """
    result = _mysql.all(sql, (question_id,))
    return result


def get_keypoint_from_solution_tag(question_id):
    """
    获取题目的知识点标签来预测聚类
    :param question_id:
    :return:
    """
    sql = """
          SELECT tag_id FROM solution_tag
          WHERE question_id = %s AND tag_type = "G"
          AND status = 1
          """
    result = _mysql.all(sql, (question_id,))
    return result


def get_question_title_by_id(question_id):
    """
    获取题目的题干
    Args:
        question_id: 题目ID
    Return:
    """
    sql = """SELECT title
            FROM solution_subtitle
            WHERE subtitle_no = 0 AND question_id = %s
        """
    result = _mysql.all(sql, (question_id,))
    return result


def get_sub_question_num_by_id(question_id):
    """
    获取题目有多少小问
    Args:
        question_id: 题目ID
    """
    sql = """SELECT count(title)
            FROM solution_subtitle
            WHERE subtitle_no > 0 AND question_id = %s
        """
    result = _mysql.all(sql, (question_id,))
    return result

if __name__ == '__main__':
    data_list = get_no_labeled_intersect_tags_questions_summary(2016)
