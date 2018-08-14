# -*- coding: utf-8 -*-
import sys
import re
import numpy as np
import keras
from lib.train.data_access import connect_db
from lib.utils.config_loader import config

reload(sys)
sys.setdefaultencoding('utf8')


class DataGen(keras.utils.Sequence):
    def __init__(self, ids, batch_size, n_classes, max_len=800, word2vector_fn=r'word2vec.txt'):
        self._ids = ids
        self._batch_size = batch_size
        self._n_classes = n_classes
        self._max_len = max_len
        self._word2vector_map = self.load_word2vector_map(word2vector_fn)

    def __len__(self):
        return int(np.floor(len(self._ids) / self._batch_size))

    def __getitem__(self, idx):
        batch_ids = self._ids[idx * self._batch_size:(idx + 1) * self._batch_size]
        X, y = self._get_data_by_ids(batch_ids)

        return X, y

    def _get_data_by_ids(self, ids):
        X, y = [], []
        X_org, y_org = self._get_org_data_by_ids(ids)

        for idx in range(len(y_org)):
            X_i = X_org[idx]
            y_i = y_org[idx]

            X_i = self.convert_text_to_vectors(X_i)
            if isinstance(y_i, list):
                # if y_i is list, sigmoid is used for output layer
                # and each class will be independent
                y_i = np.sum(keras.utils.to_categorical(y_i, num_classes=self._n_classes), axis=0)
            else:
                # if y_i is int, softmax is used for output layer
                # and each class will be related
                y_i = keras.utils.to_categorical(y_i, num_classes=self._n_classes)

            X.append(X_i)
            y.append(y_i)

        X = keras.preprocessing.sequence.pad_sequences(X, maxlen=self._max_len)
        X = np.array(X)
        y = np.array(y)

        return X, y

    def _get_org_data_by_ids(self, ids):
        raise NotImplementedError()

    def convert_text_to_vectors(self, text):
        vectors = []
        for c in text:
            vectors.append(self._word2vector_map[c])

        return vectors

    @staticmethod
    def load_word2vector_map(word2vector_fn):
        word2vector_map = {}
        first_line = True
        with open(word2vector_fn, 'r') as f:
            for line in f:
                if first_line:
                    first_line = False
                    continue
                tokens = line.rstrip().split(' ')
                word2vector_map[tokens[0].decode('utf-8')] = [float(x) for x in tokens[1:]]

        return word2vector_map


class DfcltyDataGen(DataGen):
    def __init__(self, ids, batch_size, n_classes):
        super(DfcltyDataGen, self).__init__(ids, batch_size, n_classes)

    def _get_org_data_by_ids(self, ids):
        X = []
        y = []

        mysql_conf = config.conf['mysql'][config.runtime_mode]
        connection = connect_db(**mysql_conf)

        sql_fmt = 'SELECT `ss`.`title`, `ss`.`analysis`, `ss`.`remark`, `st`.`tag_id` ' \
                  'FROM `solution` AS `ss` JOIN `solution_tag` AS `st` ' \
                  'ON `ss`.`question_id` = `st`.`question_id` ' \
                  'WHERE `ss`.`question_id` IN ({}) AND `ss`.`status` = 1 ' \
                  'AND `st`.`tag_type` = \"A\" AND `st`.`status` = 1'
        sql = sql_fmt.format(', '.join(['\"{}\"'.format(_id) for _id in ids]))
        results = connection.execute(sql).fetchall()

        for title, analysis, remark, dfclty in results:
            q_text = '{}{}{}'.format(title, analysis, remark)
            q_text = q_text.replace('\r', '')
            q_text = q_text.replace('\n', '')
            q_text = q_text.decode('utf-8')
            q_text = ''.join(re.findall(ur'[\u4e00-\u9fff]+', q_text))

            dfclty = int(dfclty[-1]) - 1  # convert 'A1' to 0

            X.append(q_text)
            y.append(dfclty)

        return X, y


class KnowlDataGen(DataGen):
    def __init__(self, ids, batch_size, n_classes, knowl2int_fn=r'knowl_info.csv'):
        super(KnowlDataGen, self).__init__(ids, batch_size, n_classes)
        self._knowl2int_map = self.load_knowl2int_map(knowl2int_fn)
        self._errors = []

    def _get_org_data_by_ids(self, ids):
        X = []
        y = []

        mysql_conf = config.conf['mysql'][config.runtime_mode]
        connection = connect_db(**mysql_conf)

        sql_fmt = 'SELECT `ss`.`title`, `ss`.`analysis`, `ss`.`remark`, GROUP_CONCAT(`st`.`tag_id`) ' \
                  'FROM `solution` AS `ss` JOIN `solution_tag` AS `st` ' \
                  'ON `ss`.`question_id` = `st`.`question_id` ' \
                  'WHERE `ss`.`question_id` IN ({}) AND `ss`.`status` = 1 ' \
                  'AND `st`.`tag_type` = \"G\" AND `st`.`status` = 1 ' \
                  'GROUP BY `ss`.`id`'
        sql = sql_fmt.format(', '.join(['\"{}\"'.format(_id) for _id in ids]))
        results = connection.execute(sql).fetchall()

        for title, analysis, remark, knowl in results:
            q_text = '{}{}{}'.format(title, analysis, remark)
            q_text = q_text.replace('\r', '')
            q_text = q_text.replace('\n', '')
            q_text = q_text.decode('utf-8')
            q_text = ''.join(re.findall(ur'[\u4e00-\u9fff]+', q_text))

            try:
                knowl_list = [self._knowl2int_map[_id] for _id in knowl.split(',')]
            except KeyError as ex:
                self._errors.append('{}:{}'.format(knowl, ex))
                continue

            X.append(q_text)
            y.append(knowl_list)

        return X, y

    @staticmethod
    def load_knowl2int_map(knowl2int_fn):
        knowl2int_map = {}
        with open(knowl2int_fn, 'r') as f:
            count = 0
            first_line = True
            for line in f:
                if first_line:
                    first_line = False
                    continue
                _id, _, _ = line.rstrip().split(';')
                knowl2int_map[_id] = count
                count += 1
        return knowl2int_map
