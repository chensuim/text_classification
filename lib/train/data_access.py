# -*- coding: utf-8 -*-
import sys
import numpy as np
from sqlalchemy import create_engine
from lib.utils.config_loader import config

reload(sys)
sys.setdefaultencoding('utf8')


def connect_db(user, passwd, host, port, db, charset):
    connection_str_fmt = 'mysql+pymysql://{}:{}@{}:{}/{}?charset={}'
    connection_str = connection_str_fmt.format(user, passwd, host, port, db, charset)
    engine = create_engine(connection_str)

    return engine.connect()


def get_q_ids(q_type, q_num=10000, train_perc=0.98, valid_perc=0.01):
    mysql_conf = config.conf['mysql'][config.runtime_mode]
    connection = connect_db(**mysql_conf)

    q_ids = []
    sql_fmt = 'SELECT `ss`.`question_id` ' \
              'FROM `solution` AS `ss` JOIN `solution_tag` AS `st` ' \
              'ON `ss`.`question_id` = `st`.`question_id` ' \
              'WHERE `ss`.`status` = 1 AND `st`.`tag_type` = \"{}\" AND `st`.`status` = 1 ' \
              'LIMIT {}'
    sql = sql_fmt.format(q_type, q_num)
    results = connection.execute(sql).fetchall()
    for result in results:
        q_ids.append(result[0])

    train_num = int(q_num * train_perc)
    valid_num = int(q_num * valid_perc)

    # shuffle ids
    np.random.shuffle(q_ids)
    train_q_ids = q_ids[:train_num]
    valid_q_ids = q_ids[train_num:train_num + valid_num]
    test_q_ids = q_ids[train_num + valid_num:]

    return train_q_ids, valid_q_ids, test_q_ids
