# -*- coding: utf-8 -*-
import sys
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from lib.train.difficulty_data_gen import DifficultyDataGen, get_data_ids

reload(sys)
sys.setdefaultencoding('utf8')


def train():
    # get train and test data
    train_ids, validation_ids, test_ids = get_data_ids(80000)
    train_gen = DifficultyDataGen(train_ids, 256)
    validation_gen = DifficultyDataGen(validation_ids, 256)
    test_gen = DifficultyDataGen(test_ids, 256)

    # create LSTM model
    class_num = 4
    model = Sequential()
    model.add(LSTM(64, input_dim=300, return_sequences=False))
    model.add(Dense(class_num, activation='softmax'))

    # compile and train model
    model.compile(loss='categorical_crossentropy', optimizer='Adamax', metrics=['accuracy'])
    print(model.summary())
    model.fit(generator=train_gen, validation_data=validation_gen, epochs=32,
              use_multiprocessing=True, workers=6)

    # test model
    scores = model.evaluate_generator(generator=test_gen)
    print("Accuracy: %.2f%%" % (scores[1] * 100))

    model.save('model_weight.h5')

