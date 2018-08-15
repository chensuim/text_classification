# -*- coding: utf-8 -*-
import sys
import argparse
from lib.utils.clock import clock
from lib.train.train_model import train_dfclty_model, train_knowl_model

reload(sys)
sys.setdefaultencoding('utf8')


@clock()
def do_train_dfclty_model():
    train_dfclty_model()


@clock()
def do_train_knowl_model():
    train_knowl_model()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='train model arguments description')
    parser.add_argument('--tkm', action="store_true", help='train knowl model')
    parser.add_argument('--tdm', action="store_true", help='train dfclty model')

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.tkm:
        do_train_knowl_model()
    elif args.tdm:
        do_train_dfclty_model()
