# -*- coding: utf-8 -*-
import sys
import numpy as np
import re
from bz2 import BZ2File as b2f
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence

reload(sys)
sys.setdefaultencoding('utf8')


def read_words_vector(path, topn=635974):
    lines_num, dim = 0, 0
    vectors = {}
    first_line = True
    with open(path, 'r') as f:
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


def get_vector_from_text(words_vector_dict, text):
    vector = []
    for c in text:
        vector.append(words_vector_dict[c])

    return vector


def load_data(question_texts_fn, num=10000, train_percentage=0.95):
    X = []
    Y = []

    words_vector_dict, _ = read_words_vector(r'word2vec.txt')
    count = 0

    with open(question_texts_fn, 'r') as f:
        for line in f:
            count += 1
            if count > num:
                break

            line = line.rstrip()
            question_id, difficulty, text = line.split(r';;')
            text = text.decode('utf-8')
            text = ''.join(re.findall(ur'[\u4e00-\u9fff]+', text))
            difficulty = int(difficulty) - 1

            feature = get_vector_from_text(words_vector_dict, text)
            predict = [0 if i != difficulty else 1 for i in range(4)]

            X.append(feature)
            Y.append(predict)

    X = sequence.pad_sequences(X, maxlen=600)
    X = np.array(X)
    Y = np.array(Y)

    m = int(len(X) * train_percentage)

    X_train, Y_train = X[:m], Y[:m]
    X_test, Y_test = X[m:], Y[m:]

    return (X_train, Y_train), (X_test, Y_test)


def train():
    # get train and test data
    (X_train, Y_train), (X_test, Y_test) = load_data(r'question_texts.txt')

    print X_train.shape
    print Y_train.shape

    # create sequence model
    class_num = 4
    model = Sequential()
    model.add(LSTM(64, input_dim=300, return_sequences=False))
    model.add(Dense(class_num, activation='softmax'))

    # compile and train model
    model.compile(loss='categorical_crossentropy', optimizer='Adamax', metrics=['accuracy'])
    print(model.summary())
    model.fit(X_train, Y_train, epochs=32, batch_size=256)

    # test model
    scores = model.evaluate(X_test, Y_test, verbose=0)
    print("Accuracy: %.2f%%" % (scores[1] * 100))

    model.save('model_weight.h5')

