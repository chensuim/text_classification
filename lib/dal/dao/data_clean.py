# coding: utf-8
import re
import argparse
import os
import sys
import json
from elasticsearch import helpers
from elasticsearch import Elasticsearch
import time
import MySQLdb
from MySQLdb.cursors import SSDictCursor
import codecs
import threadpool
import threading
import jieba
import jieba.analyse
reload(sys)
sys.setdefaultencoding('utf-8')

html_re = [
    ['((\r\n)|(\n)|(<br>)|(</br>)|(br/))', ''],
    ['<img\s.+?>', ''],
    ['((<div\s.+?>)|(<\s*/div>))', ''],
    ['\!\[((神算子)|(图片))\]\(http.+?\)', ''],
    ['((<sup>)|(</sup>)|(<sub>)|(</sub>))', ''],
    ['((<table.*?>)|(</table>)|(<tbody.*?>)|(</tbody>)|(<tr.*?>)|(</tr>)|(<td.*?>)|(</td>))', ''],
    ['((<span.*?>)|(</span>)|(<dfn.*?>))', ''],
    # 严格匹配
    ['<textarea', ''],
    ['（\s*）', ''],
    ['_+', ''],
    ['（　　）', ''],
]

def data_clean(article):
    global html_re
    for item in html_re:
        regular_expr = item[0]
        replace_word = item[1]
        regular_expr = regular_expr.encode('utf-8')
        article = re.sub(regular_expr , replace_word, article.encode('utf-8'))
    return article

