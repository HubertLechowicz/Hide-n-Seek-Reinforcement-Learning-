from gym import wrappers

from hidenseek_gym.wrappers.monitoring import stats_recorder

class MultiMonitor(wrappers.Monitor):
    def __init__(self, env, directory, video_callable=None, force=False, resume=False, write_upon_reset=False, uid=None, mode=None):
        super().__init__(env, directory, video_callable, force, resume, write_upon_reset, uid, mode)

    def _start(self, directory, video_callable=None, force=False, resume=False, write_upon_reset=False, uid=None, mode=None):
        super()._start(directory, video_callable, force, resume, write_upon_reset, uid, mode)

        self.stats_recorder = stats_recorder.StatsRecorder(directory, '{}.episode_batch.{}'.format(self.file_prefix, self.file_infix), autoreset=self.env_semantics_autoreset, env_id=self.env.spec.id)

