# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
import sys
import os
import time

reload(sys)
sys.setdefaultencoding("utf-8")


class LabelRecommendStat(object):
    def __init__(self, user, pwd, host, port, db):
        self._file_name = r'question_stat.txt'
        self._connection = None
        self._questions_tag_info = {}

        self.connect_db(user, pwd, host, port, db)
        self.load_benchmark()

    def connect_db(self, user, pwd, host, port, db):
        connection_str_fmt = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=UTF8MB4'
        connection_str = connection_str_fmt.format(user, pwd, host, port, db)
        engine = create_engine(connection_str)

        self._connection = engine.connect()

    def load_benchmark(self):
        file_path = os.path.join(os.getcwd(), r'data_test.txt')
        with open(file_path, 'r') as f:
            for line in f:
                question_id, tags_info, _ = line.split(';')
                tag_ids = set(tag_id.split('-')[1] if '-' in tag_id else tag_id for tag_id in tags_info.split('$'))
                self._questions_tag_info[question_id] = tag_ids

    def dump(self):
        sql_fmt = 'SELECT `tag_id` FROM `solution_tag` WHERE `question_id` = \"{}\"'
        lines = []

        for _id in self._questions_tag_info:
            sql = sql_fmt.format(_id)
            results = self._connection.execute(sql).fetchall()

            tags_by_ai = set(results)
            tags_by_human = self._questions_tag_info[_id]

            tp_count = len(tags_by_ai & tags_by_human)
            fp_count = len(tags_by_ai - tags_by_human)
            fn_count = len(tags_by_human - tags_by_ai)

            lines.append('{}:{},{},{}\n'.format(_id, tp_count, fp_count, fn_count))

        with open(self._file_name, 'w') as f:
            for line in lines:
                f.write(line)

    @staticmethod
    def stat(file_name):
        precision = 0.0
        recall = 0.0
        count = 0
        with open(file_name) as f:
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
        precision /= count
        recall /= count
        print 'Precision : {:.2f}'.format(precision)
        print 'Recall    : {:.2f}'.format(recall)


if __name__ == '__main__':
    _user = 'ssz_test'
    _pwd = 'zMhrIuu69ua%',
    _host = 'rm-2zeiamje1ijw7h0lldo.mysql.rds.aliyuncs.com'
    _port = 3306
    _db = 'shensz_test'

    label_recommend_stat = LabelRecommendStat(user=_user, pwd=_pwd, host=_host, port=_port, db=_db)

    start_time = time.time()
    label_recommend_stat.dump()
    end_time = time.time()
    print '\nDUMP --- {} seconds ---'.format(end_time - start_time)

    start_time = time.time()
    label_recommend_stat.stat()
    end_time = time.time()
    print '\nSTAT --- {} seconds ---'.format(end_time - start_time)
