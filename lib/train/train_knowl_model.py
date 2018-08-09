# -*- coding: utf-8 -*-
import sys
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from lib.train.knowl_data_gen import KnowlDataGen, get_data_ids

reload(sys)
sys.setdefaultencoding('utf8')


def train():
    class_num = 1575

    # get train and test data
    train_ids, validation_ids, test_ids = get_data_ids(78000)
    train_gen = KnowlDataGen(ids=train_ids, batch_size=256, n_classes=class_num)
    validation_gen = KnowlDataGen(ids=validation_ids, batch_size=256, n_classes=class_num)
    test_gen = KnowlDataGen(ids=test_ids, batch_size=256, n_classes=class_num)

    # create LSTM model
    model = Sequential()
    model.add(LSTM(128, input_shape=(None, 300), return_sequences=False))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(class_num, activation='sigmoid'))

    # compile and train model
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    print(model.summary())
    model.fit_generator(generator=train_gen, validation_data=validation_gen, epochs=32, use_multiprocessing=True, workers=6)

    # test model
    scores = model.evaluate_generator(generator=test_gen)
    print("Accuracy: %.2f%%" % (scores[1] * 100))

    model.save('knowl_model.h5')
