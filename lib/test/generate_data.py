# -*- coding: utf-8 -*-
import sys
import os
import random
from sqlalchemy import create_engine
from lib.utils.config_loader import config

reload(sys)
sys.setdefaultencoding('utf8')


def connect_db(user, passwd, host, port, db, charset):
    connection_str_fmt = 'mysql+pymysql://{}:{}@{}:{}/{}?charset={}'
    connection_str = connection_str_fmt.format(user, passwd, host, port, db, charset)
    engine = create_engine(connection_str)

    return engine.connect()


def get_question_ids_patch(connection):
    query_min_sql = 'SELECT MIN(`auto_increment_id`) FROM `solution` WHERE `status` = 1'
    results = connection.execute(query_min_sql).fetchall()
    min_id = results[0][0] if results else ''

    query_max_sql = 'SELECT MAX(`auto_increment_id`) FROM `solution` WHERE `status` = 1'
    results = connection.execute(query_max_sql).fetchall()
    max_id = results[0][0] if results else ''

    if not min_id or not max_id:
        print 'No min/max id...'
        return

    print 'Will process questions with auto_increment_id between [{}, {}]'.format(min_id, max_id)

    sql_fmt = 'SELECT `question_id` FROM `solution` WHERE `auto_increment_id` BETWEEN {} AND {} AND `status` = 1'
    ranges = range(min_id, max_id, 1000)
    ranges.append(max_id + 1)

    for i in range(len(ranges) - 1):
        sys.stdout.write('\rProcessing [{}, {})'.format(ranges[i], ranges[i + 1]))
        sys.stdout.flush()

        sql = sql_fmt.format(ranges[i], ranges[i + 1] - 1)
        results = connection.execute(sql).fetchall()
        yield [result[0] for result in results] if results else None


def generate_all_data(all_data_fn):
    mysql_conf = config.conf['mysql'][config.runtime_mode]
    connection = connect_db(**mysql_conf)

    ids_patch_generator = get_question_ids_patch(connection)
    for ids in ids_patch_generator:
        if not ids:
            continue
        lines = []
        for _id in ids:
            sql_fmt = 'SELECT `tag_id`, `tag_type`, `teach_book_id` FROM `solution_tag` ' \
                            'WHERE `question_id` = \"{}\" AND `tag_id` IS NOT NULL AND `status` = "1"'
            sql = sql_fmt.format(_id)
            results = connection.execute(sql).fetchall()

            # build question tag info string
            chapter_tags_set = set()
            difficulty_tags_set = set()
            suit_tags_set = set()
            key_point_tags_set = set()
            tags_type_set = set()
            for tag_id, tag_type, teach_book_id in results:
                tags_type_set.add(tag_type)
                if 'H' == tag_type:
                    chapter_tags_set.add('{}-{}'.format(teach_book_id, tag_id))
                if 'A' == tag_type:
                    difficulty_tags_set.add(tag_id)
                if 'B' == tag_type:
                    suit_tags_set.add(tag_id)
                if 'G' == tag_type:
                    key_point_tags_set.add(tag_id)

            # RECORD FORMAT: question_id;teach_book_id-chapter_id,$difficult_id,$suit_id,$key_point_id,;tag_type,
            tag_ids_str = '{}${}${}${}'.format(','.join(chapter_tags_set), ','.join(difficulty_tags_set),
                                               ','.join(suit_tags_set), ','.join(key_point_tags_set))
            tag_types_str = ','.join(tags_type_set)
            lines.append('{};{};{}\n'.format(_id, tag_ids_str, tag_types_str))

        file_path = os.path.join(os.getcwd(), all_data_fn)
        with open(file_path, 'a+') as f:
            for line in lines:
                f.write(line)


def generate_test_data(all_data_fn, test_data_fn, num=1000):
    questions = []
    file_path = os.path.join(os.getcwd(), all_data_fn)
    with open(file_path, 'r') as f:
        questions.extend(line.strip() for line in f)

    filter_questions = []
    for question in questions:
        tag_types = question.split(';')[2]
        if 'H' in tag_types and 'A' in tag_types and 'B' in tag_types and 'G' in tag_types:
            filter_questions.append(question)

    print '\n#filtered_questions: {}'.format(len(filter_questions))

    test_questions = random.sample(filter_questions, num)
    file_path = os.path.join(os.getcwd(), test_data_fn)
    with open(file_path, 'w') as f:
        for question in test_questions:
            f.write('{}\n'.format(question))
