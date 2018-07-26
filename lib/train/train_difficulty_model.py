# -*- coding: utf-8 -*-
import sys
import numpy as np
import re
import jieba
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence

reload(sys)
sys.setdefaultencoding('utf8')


def get_words_dict(top1k_words_fn):
    words_dict = {}
    count = 1

    with open(top1k_words_fn) as f:
        for line in f:
            word = line.rstrip()
            words_dict[word] = count
            count += 1

    return words_dict


def get_vector_from_text(words_dict, text):
    vector = []
    seg_list = jieba.cut(text, cut_all=False)
    for seg in seg_list:
        vector.append(words_dict.get(seg, 0))

    return vector


def load_data(question_texts_fn, num=1000, train_percentage=0.8):
    X = []
    Y = []

    words_dict = get_words_dict(r'top1k_words.txt')
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

            feature = get_vector_from_text(words_dict, text)
            predict = [0 if i != difficulty else 1 for i in range(4)]

            X.append(feature)
            Y.append(predict)

    X = np.array(X)
    Y = np.array(Y)

    m = int(len(X) * train_percentage)

    X_train, Y_train = X[:m], Y[:m]
    X_test, Y_test = X[m:], Y[m:]

    return (X_train, Y_train), (X_test, Y_test)


def train():
    # get train and test data
    top_words = 1000
    (X_train, Y_train), (X_test, Y_test) = load_data(r'question_texts.txt')
    max_review_length = 500
    X_train = sequence.pad_sequences(X_train, maxlen=max_review_length)
    X_test = sequence.pad_sequences(X_test, maxlen=max_review_length)

    print X_train.shape
    print Y_train.shape

    # create sequence model
    embedding_vector_length = 32
    class_num = 4
    model = Sequential()
    model.add(Embedding(top_words, embedding_vector_length, input_length=max_review_length))
    model.add(LSTM(100))
    model.add(Dense(class_num, activation='softmax'))

    # compile and train model
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop', metrics=['accuracy'])
    print(model.summary())
    model.fit(X_train, Y_train, epochs=3, batch_size=16)

    # test model
    scores = model.evaluate(X_test, Y_test, verbose=0)
    print("Accuracy: %.2f%%" % (scores[1] * 100))
