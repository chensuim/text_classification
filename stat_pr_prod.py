# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
import sys
import time

reload(sys)
sys.setdefaultencoding("utf-8")


class LabelRecommendStat(object):
    def __init__(self, user='ssz_test', pwd='zMhrIuu69ua%',
                 host='rm-2zeiamje1ijw7h0lldo.mysql.rds.aliyuncs.com', port=3306, db='shensz'):
        self._connection = None
        self.connect_db(user, pwd, host, port, db)

    def connect_db(self, user, pwd, host, port, db):
        connection_str_fmt = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=UTF8MB4'
        connection_str = connection_str_fmt.format(user, pwd, host, port, db)
        engine = create_engine(connection_str)
        self._connection = engine.connect()

    def get_question_ids(self):
        query_min_sql = 'SELECT MIN(`auto_increment_id`) FROM `solution` WHERE `status` = 1'
        results = self._connection.execute(query_min_sql).fetchall()
        min_id = results[0][0] if results else ''

        query_max_sql = 'SELECT MAX(`auto_increment_id`) FROM `solution` WHERE `status` = 1'
        results = self._connection.execute(query_max_sql).fetchall()
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
            results = self._connection.execute(sql).fetchall()
            yield results if results else None

    def dump(self, file_name):
        ids_generator = self.get_question_ids()
        for ids in ids_generator:
            if not ids:
                continue
            for _id in ids:
                self.dump_one_question(_id[0], file_name)

    def dump_one_question(self, _id, file_name):
        # true positive count
        sql_fmt = 'SELECT COUNT(*) FROM `solution_tag` ' \
                  'WHERE `question_id` = \"{}\" AND `create_user` = \"ai\" AND `status` = "1"'
        sql = sql_fmt.format(_id)
        results = self._connection.execute(sql).fetchall()
        tp_count = results[0][0] if results else 0

        # false positive count
        sql_fmt = 'SELECT COUNT(*) FROM `solution_tag` ' \
                  'WHERE `question_id` = \"{}\" AND `create_user` = \"ai\" AND `status` = "-1"'
        sql = sql_fmt.format(_id)
        results = self._connection.execute(sql).fetchall()
        fp_count = results[0][0] if results else 0

        # false negative count
        sql_fmt = 'SELECT COUNT(*) FROM `solution_tag` ' \
                  'WHERE `question_id` = \"{}\" AND `create_user` <> \"ai\" AND `status` = "1"'
        sql = sql_fmt.format(_id)
        results = self._connection.execute(sql).fetchall()
        fn_count = results[0][0] if results else 0

        with open(file_name, 'a+') as f:
            f.write('{}:{},{},{}\n'.format(_id, tp_count, fp_count, fn_count))

    def stat(self, file_name):
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
    file_name = r'question_stat.dat'

    label_recommend_stat = LabelRecommendStat()

    start_time = time.time()
    label_recommend_stat.dump(file_name)
    end_time = time.time()
    print '\nDUMP --- {} seconds ---'.format(end_time - start_time)

    start_time = time.time()
    label_recommend_stat.stat(file_name)
    end_time = time.time()
    print 'STAT --- {} seconds ---'.format(end_time - start_time)
