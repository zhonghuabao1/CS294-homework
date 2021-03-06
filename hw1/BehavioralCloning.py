#/usr/bin/env python3
import sys
import gym
import time
import pickle
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tqdm import trange, tqdm
import logz

def logger(id_, out):
    logz.log_tabular('Iteration', id_)
    logz.log_tabular('AverageReturn', out[0])
    logz.log_tabular('StdReturn', out[1])
    logz.dump_tabular()

def get_data(pkl):
    with open(pkl, 'rb') as f:
        data = pickle.loads(f.read())
        return data['observations'], data['actions'][:,0]

class DataGenerator(object):
    def __init__(self, x, y, batch_size=64):
        self.x = x
        self.y = y
        self.batch_size = batch_size
        self.n = x.shape[0]
        assert self.n > batch_size
        assert self.n == y.shape[0]
        self.index_generator = self.flow_index()

    def next(self):
        ids_batch = next(self.index_generator)
        return self.x[ids_batch], self.y[ids_batch]

    def flow_index(self):
        i = self.n
        while True:
            j = i + self.batch_size
            if j > self.n:  # reset
                ids = np.random.randint(0, self.n, self.n)
                i, j = 0, self.batch_size

            ids_batch = ids[i:j]
            i = j
            yield ids_batch

def build_model(in_shape, out_shape):
    in_tensor = keras.layers.Input([in_shape[-1]])
    x = in_tensor
    x1 = keras.layers.Dense(128, activation='relu')(x)
    x = keras.layers.Dense(256, activation='relu')(x1)
    x = keras.layers.Dense(64, activation='relu')(x)
    # x = keras.layers.add([x, x1])
    x = keras.layers.Dense(out_shape[-1], activation=None)(x)
    model = keras.Model(in_tensor, x)
    return model

class Robot(object):
    def __init__(self, envname, model, expert=None):
        self.envname = envname
        self.env = gym.make(envname)
        self.model = model
        self.expert = expert

    def save(self):
        self.model.save('./%s-BC.h5py' % self.envname)

    def rollout(self, steps=1000, render=False):
        totalr = 0.
        obs = self.env.reset()
        for i in range(steps):
            action = self.model.predict(obs[None, :])[0]
            obs, r, done, _ = self.env.step(action)
            totalr += r

            if render: self.env.render()
            if done: break
        return totalr

    def test_in_env(self, rollouts):
        rs = [self.rollout() for i in range(rollouts)]
        out = (np.mean(rs), np.std(rs))
        return out

    def fit_generator(self, data_gen, epochs=1):
        out = self.test_in_env(rollouts)
        logger(0, out)

        outs = []
        for i in range(epochs):
            print("epochs %d/%d:" % (i+1, epochs))

            pbar = tqdm(range(20 * data_gen.n // batch_size))
            for j in pbar:
                x_batch, y_batch = data_gen.next()
                loss = self.model.train_on_batch(x_batch, y_batch)
                pbar.set_description("loss(%f)" % (loss))
            out = self.test_in_env(rollouts)
            logger(i+1, out)

if __name__ == '__main__':
    envname = 'Hopper-v2' if len(sys.argv) < 2 else sys.argv[1]
    epochs = 10
    rollouts = 20
    batch_size = 256
    logz.configure_output_dir("./log/"+envname+"_BC_"+time.strftime("%Y-%m-%d_%H-%M-%S"))

    x, y = get_data('./expert_data/%s.pkl' % envname)
    print(x.shape, y.shape)
    data_gen = DataGenerator(x, y, batch_size)

    model = build_model(x.shape, y.shape)
    model.summary()

    # opt = keras.optimizers.SGD(momentum=0.9)
    opt = keras.optimizers.Adam()
    model.compile(loss='mse', optimizer=opt)
    robot = Robot(envname, model)

    # keras 自带的fit()得到的reward差很多，不知道是为什么
    robot.fit_generator(data_gen, epochs)

    print('\n\n----------------------------------------')
    robot.rollout(render=True)
