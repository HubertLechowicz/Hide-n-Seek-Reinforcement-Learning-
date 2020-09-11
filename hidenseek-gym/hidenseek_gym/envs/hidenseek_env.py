import gym
from gym import error, spaces, utils
from gym.utils import seeding


class HideNSeekEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        pass

    def step(self, action_n):
        obs_n = list()
        reward_n = list()
        done_n = list()
        info_n = {'n': []}

        return obs_n, reward_n, done_n, info_n

    def reset(self):
        pass

    def render(self, mode='human', close=False):
        pass
