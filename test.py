# -*- coding: utf-8 -*-
import sys
import argparse
import logging
from lib.utils.config_loader import config
from lib.utils.clock import clock
from lib.test.generate_data import generate_all_data, generate_test_data, \
    generate_q_knowl
from lib.test.stat_pr import stat_prod, stat_test
from lib.test.test_model import test_model

reload(sys)
sys.setdefaultencoding('utf8')

test_data_fn = r'data_test.txt'
all_data_fn = r'data_all.txt'
q_dfclty_fn = r'q_dfclty.txt'
q_knowl_fn = r'q_knowl.txt'
knowl_info_fn = r'knowl_info.csv'

# 设定requests库log级别
logging.config.dictConfig(config.conf['web_logging'])


@clock()
def generate_whole_data_with_labels():
    generate_all_data(all_data_fn)


@clock()
def generate_test_data_with_labels():
    generate_test_data(all_data_fn, test_data_fn)


@clock()
def stat_pr_prod():
    stat_prod()


@clock()
def stat_pr_test():
    stat_test(test_data_fn)


@clock()
def test():
    test_model(test_data_fn)


@clock()
def train_knowl_model():
    generate_q_knowl(q_knowl_fn=q_knowl_fn, knowl_info_fn=knowl_info_fn)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='test model arguments description')
    parser.add_argument('--G', action="store_true", help='generate whole data with labels')
    parser.add_argument('--g', action="store_true", help='generate test data with labels')
    parser.add_argument('--S', action="store_true", help='stat precision/recall for prod env')
    parser.add_argument('--s', action="store_true", help='stat precision/recall for test env')
    parser.add_argument('--t', action="store_true", help='test model, update write_info_to_mysql.py before run test')
    parser.add_argument('--tkm', action="store_true", help='train knowl model')

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.G:
        generate_whole_data_with_labels()
    elif args.g:
        generate_test_data_with_labels()
    elif args.S:
        stat_pr_prod()
    elif args.s:
        stat_pr_test()
    elif args.t:
        test()
    elif args.tkm:
        train_knowl_model()
