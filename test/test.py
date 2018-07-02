# -*- coding: utf-8 -*-
import logging.config
import sys
import os
import time
from collections import defaultdict
from lib.utils.config_loader import config
from lib.dal.label_questions_info import label_summary_tags_for_questions

reload(sys)
sys.setdefaultencoding('utf8')

# 配置实例
conf = config.conf
logging.getLogger("requests").setLevel(logging.ERROR)
logging.config.dictConfig(conf['web_logging'])
_logger = logging.getLogger("root." + __name__)


def get_test_data():
    """
    RECORD FORMAT: question_id;teach_book_id-chapter_id,$difficult_id,$suit_id,$key_point_id,;tag_type,
    :return:
    """
    questions_info = []
    file_path = os.path.join(os.getcwd(), r'data_test.txt')
    with open(file_path, 'r') as f:
        questions_info.extend(line.split(';') for line in f)

    questions_test = defaultdict(list)

    for question_id, tag_ids, tag_types in questions_info:
        if 'H' in tag_types:
            chapters_info = tag_ids.split('$')[0].split(',')
            teach_book_ids = set()
            for teach_book_id, _ in (chapter_info.split('-') for chapter_info in chapters_info):
                teach_book_ids.add(teach_book_id)

            questions_test[question_id].extend("chapter{}".format(teach_book_id) for teach_book_id in teach_book_ids)

        if 'A' in tag_types:
            questions_test[question_id].append('difficulty')

        if 'B' in tag_types:
            questions_test[question_id].append('suit')

        if 'G' in tag_types:
            questions_test[question_id].append('keypoint')

    return questions_test


def test_model():
    """
    测试模型
    :return:
    """

    _logger.info('start to test new model...')

    try:
        test_data = get_test_data()
        label_summary_tags_for_questions(test_data)
    except Exception as e:
        _logger.error("exception --->>>: %s", e)


if __name__ == '__main__':
    start_time = time.time()
    test_model()
    _logger.info('finish testing new model, elapsed time: %.2fs', (time.time() - start_time))
