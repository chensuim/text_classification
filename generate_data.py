# -*- coding: utf-8 -*-
import sys
import os
import random
from lib.utils.data_source_factory import DataSourceFactory

reload(sys)
sys.setdefaultencoding('utf8')


class DataGenerator(object):
    def __init__(self):
        self._mysql = DataSourceFactory().get_mysql_client()
        self._data_all_file_name = 'data_all.txt'
        self._data_test_file_name = 'data_test.txt'

    def generate_all_data(self):
        query_min_sql = 'SELECT MIN(`id`) FROM `solution_tag` WHERE `status` = 1'
        results = self._mysql.all(query_min_sql, show_log=False)
        min_id = results[0] if results else -1

        query_max_sql = 'SELECT MAX(`id`) FROM `solution_tag` WHERE `status` = 1'
        results = self._mysql.all(query_max_sql, show_log=False)
        max_id = results[0] if results else -1

        if min_id == -1 or max_id == -1:
            print 'No min/max id...'
            return

        print 'Will process data with id between {} and {}'.format(min_id, max_id)
        sql_fmt = 'SELECT `question_id` FROM `solution_tag` WHERE `id` BETWEEN {} AND {} AND `status` = 1'
        ranges = range(min_id, max_id, 10000)
        ranges.append(max_id + 1)

        for i in range(len(ranges) - 1):
            sys.stdout.write('\rProcessing [{}, {})'.format(ranges[i], ranges[i + 1]))
            sys.stdout.flush()
            sql = sql_fmt.format(ranges[i], ranges[i + 1] - 1)
            results = self._mysql.all(sql, show_log=False)

            file_path = os.path.join(os.getcwd(), self._data_all_file_name)
            with open(file_path, 'a') as f:
                for question_id in results:
                    f.write('{}\n'.format(question_id))

    def generate_test_data(self, num=10000):
        question_ids = []
        file_path = os.path.join(os.getcwd(), self._data_all_file_name)
        with open(file_path, 'r') as f:
            question_ids.extend(line.strip() for line in f)

        test_question_ids = random.sample(question_ids, num)
        file_path = os.path.join(os.getcwd(), self._data_test_file_name)
        with open(file_path, 'w') as f:
            for question_id in test_question_ids:
                f.write('{}\n'.format(question_id))


if __name__ == '__main__':
    data_generator = DataGenerator()
    #data_generator.generate_all_data()
    data_generator.generate_test_data()
