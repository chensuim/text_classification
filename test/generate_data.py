# -*- coding: utf-8 -*-
import sys
import os
import random
import time
from lib.utils.data_source_factory import DataSourceFactory

reload(sys)
sys.setdefaultencoding('utf8')


class DataGenerator(object):
    def __init__(self):
        self._mysql = DataSourceFactory().get_mysql_client()
        self._data_all_file_name = 'data_all.txt'
        self._data_test_file_name = 'data_test.txt'

    def generate_all_data(self):
        # get valid min id
        query_min_sql = 'SELECT MIN(`auto_increment_id`) FROM `solution` WHERE `status` = 1'
        results = self._mysql.all(query_min_sql, show_log=False)
        min_id = results[0] if results else -1

        # get valid max id
        query_max_sql = 'SELECT MAX(`auto_increment_id`) FROM `solution` WHERE `status` = 1'
        results = self._mysql.all(query_max_sql, show_log=False)
        max_id = results[0] if results else -1

        if min_id == -1 or max_id == -1:
            print '\nNo min/max id...'
            return

        print '\nWill process data with auto_increment_id between {} and {}'.format(min_id, max_id)
        query_question_sql_fmt = 'SELECT `question_id` FROM `solution` ' \
                                 'WHERE `auto_increment_id` BETWEEN {} AND {} AND `status` = 1'
        ranges = range(min_id, max_id, 10000)
        ranges.append(max_id + 1)

        # process question ids per 10k records
        for i in range(len(ranges) - 1):
            sys.stdout.write('\rProcessing [{}, {})'.format(ranges[i], ranges[i + 1]))
            sys.stdout.flush()
            query_question_sql = query_question_sql_fmt.format(ranges[i], ranges[i + 1] - 1)
            question_ids = self._mysql.all(query_question_sql, show_log=False)

            question_tags_info = []
            for question_id in question_ids:
                query_tag_sql_fmt = 'SELECT `tag_id`, `tag_type`, `teach_book_id` FROM `solution_tag` ' \
                          'WHERE `question_id` = \"{}\" AND `tag_id` IS NOT NULL AND `status` = "1"'
                query_tag_sql = query_tag_sql_fmt.format(question_id)
                tags_info = self._mysql.all(query_tag_sql, show_log=False)
                if not tags_info:
                    continue
                # build question tag info string
                chapter_tags_set = set()
                difficulty_tags_set = set()
                suit_tags_set = set()
                key_point_tags_set = set()
                tags_type_set = set()
                for tag_id, tag_type, teach_book_id in tags_info:
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
                question_tags_info.append('{};{};{}'.format(question_id, tag_ids_str, tag_types_str))

            file_path = os.path.join(os.getcwd(), self._data_all_file_name)
            with open(file_path, 'a') as f:
                for question_tag_info in question_tags_info:
                    f.write('{}\n'.format(question_tag_info))

    def generate_test_data(self, num=1000):
        questions = []
        file_path = os.path.join(os.getcwd(), self._data_all_file_name)
        with open(file_path, 'r') as f:
            questions.extend(line.strip() for line in f)

        filter_questions = []
        for question in questions:
            tag_types = question.split(';')[2]
            if 'H' in tag_types and 'A' in tag_types and 'B' in tag_types and 'G' in tag_types:
                filter_questions.append(question)

        print '\n#filtered_questions: {}'.format(len(filter_questions))

        test_questions = random.sample(filter_questions, num)
        file_path = os.path.join(os.getcwd(), self._data_test_file_name)
        with open(file_path, 'w') as f:
            for question in test_questions:
                f.write('{}\n'.format(question))


if __name__ == '__main__':
    data_generator = DataGenerator()

    start_time = time.time()
    data_generator.generate_all_data()
    print '\nGenerate all data --- {} seconds ---'.format(time.time() - start_time)

    start_time = time.time()
    data_generator.generate_test_data()
    print '\nGenerate test data --- {} seconds ---'.format(time.time() - start_time)
