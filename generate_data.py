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
        query_min_sql = 'SELECT MIN(`auto_increment_id`) FROM `solution` WHERE `status` = 1'
        results = self._mysql.all(query_min_sql, show_log=False)
        min_id = results[0] if results else -1

        query_max_sql = 'SELECT MAX(`auto_increment_id`) FROM `solution` WHERE `status` = 1'
        results = self._mysql.all(query_max_sql, show_log=False)
        max_id = results[0] if results else -1

        if min_id == -1 or max_id == -1:
            print 'No min/max id...'
            return

        print 'Will process data with auto_increment_id between {} and {}'.format(min_id, max_id)
        sql_fmt = 'SELECT `question_id` FROM `solution` WHERE `auto_increment_id` BETWEEN {} AND {} AND `status` = 1'
        ranges = range(min_id, max_id, 10000)
        ranges.append(max_id + 1)

        for i in range(len(ranges) - 1):
            sys.stdout.write('\rProcessing [{}, {})'.format(ranges[i], ranges[i + 1]))
            sys.stdout.flush()
            sql = sql_fmt.format(ranges[i], ranges[i + 1] - 1)
            question_ids = self._mysql.all(sql, show_log=False)

            question_tag_info = {}
            for question_id in question_ids:
                query_tag_sql_fmt = 'SELECT `tag_id` FROM `solution_tag` ' \
                          'WHERE `question_id` = \"{}\" AND `tag_id` IS NOT NULL AND `status` = "1"'
                query_tag_sql = query_tag_sql_fmt.format(question_id)
                tag_ids = self._mysql.all(query_tag_sql, show_log=False)
                if tag_ids:
                    question_tag_info[question_id] = ','.join(tag_ids)

            file_path = os.path.join(os.getcwd(), self._data_all_file_name)
            with open(file_path, 'a') as f:
                for k, v in question_tag_info.iteritems():
                    f.write('{}:{}\n'.format(k, v))

    def generate_test_data(self, num=1000):
        questions = []
        file_path = os.path.join(os.getcwd(), self._data_all_file_name)
        with open(file_path, 'r') as f:
            questions.extend(line.strip() for line in f)

        test_questions = random.sample(questions, num)
        file_path = os.path.join(os.getcwd(), self._data_test_file_name)
        with open(file_path, 'w') as f:
            for question in test_questions:
                f.write('{}\n'.format(question))


if __name__ == '__main__':
    data_generator = DataGenerator()
    data_generator.generate_all_data()
    data_generator.generate_test_data()
