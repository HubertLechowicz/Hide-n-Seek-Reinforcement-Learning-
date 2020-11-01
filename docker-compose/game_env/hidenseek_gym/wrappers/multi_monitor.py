from gym import wrappers
import os

from gym.wrappers.monitoring import video_recorder
from game_env.hidenseek_gym.wrappers.monitoring import stats_recorder


class MultiMonitor(wrappers.Monitor):
    def __init__(self, env, directory, video_callable=None, force=False, resume=False, write_upon_reset=False, uid=None, mode=None, config={}):
        self.config = config
        super().__init__(env, directory, video_callable,
                         force, resume, write_upon_reset, uid, mode)

    def _start(self, directory, video_callable=None, force=False, resume=False, write_upon_reset=False, uid=None, mode=None):
        super()._start(directory, video_callable, force, resume, write_upon_reset, uid, mode)

        self.stats_recorder = stats_recorder.StatsRecorder(
            self.config, directory, f'{self.file_prefix}.episode_batch', autoreset=self.env_semantics_autoreset, env_id=self.env.spec.id)

    def _video_enabled(self):
        return self.config['video']['monitoring'] and self.video_callable(self.episode_id)

    def reset_video_recorder(self):
        # Close any existing video recorder
        if self.video_recorder:
            self._close_video_recorder()

        # Start recording the next video.
        ep_id = '{:09}'.format(self.episode_id)
        self.video_recorder = video_recorder.VideoRecorder(
            env=self.env,
            base_path=os.path.join(
                self.directory, f'{self.file_prefix}.video.episode{ep_id}'),
            metadata={'episode_id': self.episode_id},
            enabled=self._video_enabled(),
        )
        self.video_recorder.capture_frame()
