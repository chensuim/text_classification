# coding: utf-8
# 声明flask服务器
# 配置日志格式
import logging.config
import os
import sys
import time

logging.getLogger("requests").setLevel(logging.ERROR)
# sys.path有很多utils的目录，放在前面才能找到相关module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
# 加载配置
from utils.config_loader import config

# 配置实例
conf = config.conf
logging.config.dictConfig(conf['web_logging'])
_logger = logging.getLogger("root." + __name__)
# 加载数据接口
from dal import label_questions_info as label

# 编码问题
reload(sys)
sys.setdefaultencoding('utf8')


def main(year):
    """
    批量化题目聚类自动标定
    Args：
        year: 需要标定的试题的年份
    """
    #  处理具体年份
    if year is not None and year < 1996 or year > 2018:
        _logger.info('题目年份有误 : %s ', year)
        return None
    _logger.info('批量化题目聚类标定....')
    # 错误
    errors = []
    # 如果没有错误
    if len(errors) == 0:
        _logger.info("开始获取 %s年 未标定的题目", (year))
        try:
            label.label_cluster_for_questions(year)
            label.label_tags_for_questions_summary(year)
        except Exception as v:
            _logger.error("exception --->>>: %s", v)
            if isinstance(v, ValueError) and isinstance(v.message, tuple):
                _logger.error(v.message)
                errors.append(v.message[0])

                # 处理错误信息


if __name__ == '__main__':
    """
    parser = OptionParser()
    parser.add_option('-y', '--year',
                      action='store', dest='Year', type='int', default=2017,
                      help='请输入要聚类的年份')
    options, _ = parser.parse_args()
    """
    start_time = time.time()
    # years = [2014, 2015, 2016, 2017]
    years = range(1996, 2019) + [None]
    for year in years:
        main(year)
    _logger.info('自动标定聚类结束，耗时 %.2fs', (time.time() - start_time))
