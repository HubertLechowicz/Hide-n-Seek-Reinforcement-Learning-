from gym.envs.registration import register

register(
    id='hidenseek-v1',
    entry_point='game_env.hidenseek_gym.envs:HideNSeekEnv',
)
