import time
import json

from gym import error
from gym.wrappers.monitoring import stats_recorder

from gym.utils import atomic_write
from gym.utils.json_utils import json_encode_np


class StatsRecorder(stats_recorder.StatsRecorder):
    def __init__(self, config, directory, file_prefix, autoreset=False, env_id=None):
        super().__init__(directory, file_prefix, autoreset, env_id)

        self.rewards = []
        self.config = config
        self.episode_winners = []

    def before_step(self, action):
        assert not self.closed

        if self.done[0]:
            raise error.ResetNeeded(
                "Trying to step environment which is currently done. While the monitor is active for {}, you cannot step beyond the end of an episode. Call 'env.reset()' to start the next episode.".format(self.env_id))
        elif self.steps is None:
            raise error.ResetNeeded(
                "Trying to step an environment before reset. While the monitor is active for {}, you must call 'env.reset()' before taking an initial step.".format(self.env_id))

    def after_step(self, observation, reward, done, info):
        self.steps += 1
        self.total_steps += 1
        self.rewards.append(reward)
        self.done = done

        print(done)

        if done[0]:
            self.save_complete()

        if done[0] and self.autoreset:
            self.before_reset()
            self.after_reset(observation)

    def before_reset(self):
        assert not self.closed

        if self.done is not None and not self.done[0] and self.steps > 0:
            raise error.Error(
                "Tried to reset environment which is not done. While the monitor is active for {}, you cannot call reset() unless the episode is over.".format(self.env_id))

        self.done = [False, None]
        if self.initial_reset_timestamp is None:
            self.initial_reset_timestamp = time.time()

    def after_reset(self, observation):
        self.steps = 0
        self.rewards = []
        self.episode_types.append(self._type)

    def save_complete(self):
        if self.steps is not None:
            self.episode_lengths.append(self.steps)
            self.episode_rewards.append(self.rewards)
            self.episode_winners.append(self.done[1])
            self.timestamps.append(time.time())

    def flush(self):
        if self.closed:
            return

        with atomic_write.atomic_write(self.path) as f:
            json.dump({
                'initial_reset_timestamp': self.initial_reset_timestamp,
                'timestamps': self.timestamps,
                'config': self.config,
                'episode_lengths': self.episode_lengths,
                'episode_rewards': self.episode_rewards,
                'episode_winners': self.episode_winners,
                'episode_types': self.episode_types,
            }, f, default=json_encode_np)
