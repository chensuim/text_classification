# -*- coding: utf-8 -*-
import sys
import re
import numpy as np
import keras

reload(sys)
sys.setdefaultencoding('utf8')


def get_data_ids(num=10000, train_percentage=0.98, validation_percentage=0.01,
                 question_texts_fn=r'question_texts.txt'):
    ids = []
    count = 0

    with open(question_texts_fn, 'r') as f:
        for line in f:
            count += 1
            if count > num:
                break

            line = line.rstrip()
            question_id, difficulty, text = line.split(r';;')
            ids.append(question_id)

    m = int(num * train_percentage)
    v = int(num * validation_percentage)

    # shuffle ids
    np.random.shuffle(ids)
    train_ids = ids[:m]
    validation_ids = ids[m:m + v]
    test_ids = ids[m + v:]

    return train_ids, validation_ids, test_ids


class DifficultyDataGen(keras.utils.Sequence):
    def __init__(self, ids, batch_size, n_classes=4,
                 data_source_fn=r'question_texts.txt', words_vector_fn=r'word2vec.txt'):
        self.ids = ids
        self.batch_size = batch_size
        self.n_classes = n_classes
        self.data_source_fn = data_source_fn
        self.words_vector_dict, _ = self.read_words_vector(words_vector_fn)

    def __len__(self):
        return int(np.floor(len(self.ids) / self.batch_size))

    def __getitem__(self, idx):
        batch_ids = self.ids[idx * self.batch_size:(idx + 1) * self.batch_size]
        X, y = self._get_data_by_ids(batch_ids)

        return X, y

    def _get_data_by_ids(self, ids):
        X = []
        y = []

        with open(self.data_source_fn, 'r') as f:
            for line in f:
                line = line.rstrip()
                question_id, difficulty, text = line.split(r';;')

                if question_id not in ids:
                    continue

                text = text.decode('utf-8')
                text = ''.join(re.findall(ur'[\u4e00-\u9fff]+', text))
                difficulty = int(difficulty) - 1

                X_i = self.get_vector_from_text(text)
                y_i = keras.utils.to_categorical(difficulty, num_classes=self.n_classes)

                X.append(X_i)
                y.append(y_i)

        X = keras.preprocessing.sequence.pad_sequences(X, maxlen=800)
        X = np.array(X)
        y = np.array(y)

        return X, y

    def get_vector_from_text(self, text):
        vector = []
        for c in text:
            vector.append(self.words_vector_dict[c])

        return vector

    @staticmethod
    def read_words_vector(words_vector_fn, topn=635974):
        lines_num, dim = 0, 0
        vectors = {}
        first_line = True
        with open(words_vector_fn, 'r') as f:
            for line in f:
                if first_line:
                    first_line = False
                    dim = int(line.rstrip().split()[1])
                    continue
                lines_num += 1
                tokens = line.rstrip().split(' ')
                vectors[tokens[0].decode('utf-8')] = [float(x) for x in tokens[1:]]
                if topn != 0 and lines_num >= topn:
                    break

        return vectors, dim
