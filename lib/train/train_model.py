# -*- coding: utf-8 -*-
import sys
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from lib.train.data_gen import DfcltyDataGen, KnowlDataGen, ChapterDataGen
from lib.train.data_access import get_q_ids

reload(sys)
sys.setdefaultencoding('utf8')


def train_dfclty_model():
    # get train, validation and test data generator
    q_type = 'A'
    q_num = 80000
    batch_size = 256
    class_num = 4

    train_q_ids, valid_q_ids, test_q_ids = get_q_ids(q_type, q_num)
    train_gen = DfcltyDataGen(train_q_ids, batch_size, class_num)
    valid_gen = DfcltyDataGen(valid_q_ids, batch_size, class_num)
    test_gen = DfcltyDataGen(test_q_ids, batch_size, class_num)

    # create LSTM model
    model = Sequential()
    model.add(LSTM(class_num * 4, input_shape=(None, 300), return_sequences=False))
    model.add(Dense(class_num, activation='softmax'))

    # compile and train model
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    print(model.summary())
    model.fit_generator(generator=train_gen, validation_data=valid_gen, epochs=128, use_multiprocessing=True, workers=8)

    # test model
    scores = model.evaluate_generator(generator=test_gen)
    print("[Dfclty Model]Accuracy: %.2f%%" % (scores[1] * 100))

    model.save('./res/dfclty_model.h5')


def train_knowl_model():
    # get train, validation and test data generator
    q_type = 'G'
    q_num = 80000
    batch_size = 256
    class_num = 1575

    train_q_ids, valid_q_ids, test_q_ids = get_q_ids(q_type, q_num)
    train_gen = KnowlDataGen(train_q_ids, batch_size, class_num)
    valid_gen = KnowlDataGen(valid_q_ids, batch_size, class_num)
    test_gen = KnowlDataGen(test_q_ids, batch_size, class_num)

    # create LSTM model
    model = Sequential()
    model.add(LSTM(128, input_shape=(None, 300), return_sequences=False))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(class_num, activation='sigmoid'))

    # compile and train model
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    print(model.summary())
    model.fit_generator(generator=train_gen, validation_data=valid_gen, epochs=2, use_multiprocessing=True, workers=6)

    # test model
    scores = model.evaluate_generator(generator=test_gen)
    print("[Knowl Model]Accuracy: %.2f%%" % (scores[1] * 100))

    model.save('./res/knowl_model.h5')


def train_chapter_model():
    # get train, validation and test data generator
    q_type = 'H'
    q_num = 80000
    batch_size = 256
    class_num = 2369

    train_q_ids, valid_q_ids, test_q_ids = get_q_ids(q_type, q_num)
    train_gen = ChapterDataGen(train_q_ids, batch_size, class_num)
    valid_gen = ChapterDataGen(valid_q_ids, batch_size, class_num)
    test_gen = ChapterDataGen(test_q_ids, batch_size, class_num)

    # create LSTM model
    model = Sequential()
    model.add(LSTM(128, input_shape=(None, 300), return_sequences=False))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(class_num, activation='sigmoid'))

    # compile and train model
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    print(model.summary())
    model.fit_generator(generator=train_gen, validation_data=valid_gen, epochs=2, use_multiprocessing=True, workers=6)

    # test model
    scores = model.evaluate_generator(generator=test_gen)
    print("[Chapter Model]Accuracy: %.2f%%" % (scores[1] * 100))

    model.save('./res/chapter_model.h5')
