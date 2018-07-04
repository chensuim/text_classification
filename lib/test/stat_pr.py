# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
import sys
import os
from lib.utils.config_loader import config

reload(sys)
sys.setdefaultencoding("utf-8")


def connect_db(user, passwd, host, port, db, charset):
    connection_str_fmt = 'mysql+pymysql://{}:{}@{}:{}/{}?charset={}'
    connection_str = connection_str_fmt.format(user, passwd, host, port, db, charset)
    engine = create_engine(connection_str)

    return engine.connect()


def load_test_data(test_data_fn):
    questions_tag_info = {}

    file_path = os.path.join(os.getcwd(), test_data_fn)
    with open(file_path, 'r') as f:
        for line in f:
            question_id, tags_info, _ = line.split(';')
            tag_ids = set()
            for tag_ids_info in tags_info.split('$'):
                for tag_id in tag_ids_info.split(','):
                    tag_ids.add(tag_id.split('-')[1] if '-' in tag_id else tag_id)
            questions_tag_info[question_id] = tag_ids

    return questions_tag_info


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

    sql_fmt = 'SELECT `question_id` FROM `solution` WHERE `auto_increment_id` BETWEEN {} AND {} AND `status` = 1'
    ranges = range(min_id, max_id, 1000)
    ranges.append(max_id + 1)

    for i in range(len(ranges) - 1):
        sys.stdout.write('\rProcessing [{}, {})'.format(ranges[i], ranges[i + 1]))
        sys.stdout.flush()

        sql = sql_fmt.format(ranges[i], ranges[i + 1] - 1)
        results = connection.execute(sql).fetchall()
        yield [result[0] for result in results] if results else None


def dump_one_question(_id, connection):
    sql_fmt = 'SELECT `tag_id` FROM `solution_tag` ' \
              'WHERE `question_id` = \"{}\" AND `create_user` = \"ai\"'
    sql = sql_fmt.format(_id)
    results = connection.execute(sql).fetchall()
    tags_by_ai = set(result[0] for result in results)

    sql_fmt = 'SELECT `tag_id` FROM `solution_tag` ' \
              'WHERE `question_id` = \"{}\" AND `status` = "1"'
    sql = sql_fmt.format(_id)
    results = connection.execute(sql).fetchall()
    tags_by_human = set(result[0] for result in results)

    tp_count = len(tags_by_ai & tags_by_human)
    fp_count = len(tags_by_ai - tags_by_human)
    fn_count = len(tags_by_human - tags_by_ai)

    return '{}:{},{},{}\n'.format(_id, tp_count, fp_count, fn_count)


def dump_prod(dump_fn):
    mysql_conf = config.conf['mysql'][config.runtime_mode]
    connection = connect_db(**mysql_conf)

    ids_patch_generator = get_question_ids_patch(connection)
    for ids in ids_patch_generator:
        if not ids:
            continue
        lines = []
        for _id in ids:
            lines.append(dump_one_question(_id, connection))

        with open(dump_fn, 'a+') as f:
            for line in lines:
                f.write(line)


def dump_test(dump_fn, test_data_fn):
    mysql_conf = config.conf['mysql']['test']
    connection = connect_db(**mysql_conf)

    questions_tag_info = load_test_data(test_data_fn)

    sql_fmt = 'SELECT `tag_id` FROM `solution_tag` WHERE `question_id` = \"{}\"'
    lines = []

    for _id in questions_tag_info:
        sql = sql_fmt.format(_id)
        results = connection.execute(sql).fetchall()

        tags_by_ai = set(result[0] for result in results)
        tags_by_human = questions_tag_info[_id]

        tp_count = len(tags_by_ai & tags_by_human)
        fp_count = len(tags_by_ai - tags_by_human)
        fn_count = len(tags_by_human - tags_by_ai)

        lines.append('{}:{},{},{}\n'.format(_id, tp_count, fp_count, fn_count))

    with open(dump_fn, 'w') as f:
        for line in lines:
            f.write(line)


def stat(stat_fn):
    precision = 0.0
    recall = 0.0
    count = 0
    with open(stat_fn) as f:
        for line in f:
            _, q_stat = line.split(':')
            tp, fp, fn = q_stat.split(',')
            tp = float(tp)
            fp = float(fp)
            fn = float(fn)
            # if ai has no recommendation, pass
            if tp + fp == 0:
                continue
            # if no manual labels, pass
            if tp + fn == 0:
                continue
            count += 1
            precision += tp / (tp + fp)
            recall += tp / (tp + fn)
    if count > 0:
        precision /= count
        recall /= count
    else:
        precision = float('nan')
        recall = float('nan')
    print 'Precision : {:.2f}'.format(precision)
    print 'Recall    : {:.2f}'.format(recall)


def stat_prod():
    dump_fn = r'stat_pr_prod.txt'
    dump_prod(dump_fn)
    stat(dump_fn)


def stat_test(test_data_fn):
    dump_fn = r'stat_pr_test.txt'
    dump_test(dump_fn, test_data_fn)
    stat(dump_fn)
