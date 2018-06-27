# -*- coding: utf-8 -*-
import logging.config
import sys
import time
from lib.utils.config_loader import config
from lib.dal import label_questions_info as label

reload(sys)
sys.setdefaultencoding('utf8')

# 配置实例
conf = config.conf
logging.getLogger("requests").setLevel(logging.ERROR)
logging.config.dictConfig(conf['web_logging'])
_logger = logging.getLogger("root." + __name__)


def main(year):
    """
    批量化题目聚类自动标定
    Args：
        year: 需要标定的试题的年份
    """
    if year < 1996 or year > 2018:
        _logger.info('题目年份有误 : %s ', year)
        return None

    _logger.info('批量化题目聚类标定....')
    _logger.info("开始获取%s年未标定的题目", year)

    try:
        label.label_cluster_for_questions(year)
        label.label_tags_for_questions_summary(year)
    except Exception as e:
        _logger.error("exception --->>>: %s", e)


if __name__ == '__main__':
    start_time = time.time()
    years = range(1996, 2019)
    for year in years:
        main(year)
    _logger.info('自动标定聚类结束，耗时 %.2fs', (time.time() - start_time))
