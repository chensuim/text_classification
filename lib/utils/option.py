# coding: utf-8
import argparse

class Options(object):
    def __init__(self):
        self._parser = argparse.ArgumentParser()
        self._parser.add_argument('--input', type = str)
        self._parser.add_argument('--output', type = str)
        self._parser.add_argument('--model', type = str, default='thulac', help='model: [thulac, jieba]')
    @property
    def args(self):
        return self._parser.parse_args()

options = Options().args

if __name__ == '__main__':
    opt = Options()
