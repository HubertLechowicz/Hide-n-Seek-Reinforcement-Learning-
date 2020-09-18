import gym
import hidenseek_gym
from gym import wrappers
from hidenseek_gym import wrappers as multi_wrappers

if __name__ == '__main__':
    env = gym.make('hidenseek-v0')

    # env = wrappers.Monitor(env, directory='logs', force=True)
    env.seed(0)

    # agent_n = [hidenseek_gym.controllable.Hiding(...), hidenseek_gym.controllable.Seeker(...)]

    env = multi_wrappers.MultiMonitor(env, 'monitor', force=True)

    episode_count = 100
    reward = 0
    done_n = [False, False]

    for i in range(episode_count):
        ob = env.reset()
        print(f"EPISODE #{(i + 1)}")
        while True:
            print("\tNext Move")
            env.render()

            # action_n = agent.act(ob, reward, done) # should be some function to choose action
            action_n = [1, 1]  # temp
            obs_n, reward_n, done_n, _ = env.step(action_n)

            if all(done_n):
                break

    # Close the env and write monitor result info to disk
    env.close()
