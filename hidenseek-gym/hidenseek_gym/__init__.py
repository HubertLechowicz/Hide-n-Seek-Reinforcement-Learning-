from gym.envs.registration import register

register(
    id='hidenseek-v0',
    entry_point='hidenseek_gym.envs:HideNSeekEnv',
)