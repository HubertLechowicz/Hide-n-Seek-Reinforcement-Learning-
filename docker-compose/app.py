import multiprocessing
from flask import Flask, render_template, jsonify
from celery import Celery, group
from celery.result import AsyncResult
import time
import random

import gym
import game_env.hidenseek_gym
from gym import wrappers
from game_env.hidenseek_gym import wrappers as multi_wrappers

app = Flask(__name__)
celery = Celery(broker='redis://redis:6379/0', backend='redis://redis:6379/0')


@celery.task(name='sleep.quartet', bind=True)
def train(self):
    start = time.time()
    episodes = 2  # should be from FORM
    render_mode = 'console'

    env = gym.make('hidenseek-v0')
    env.seed(0)
    # env = multi_wrappers.MultiMonitor(env, 'monitor', force=True) # -> xvfb crash
    done_n = [False, False]

    for i in range(episodes):
        episode_nr = f'Episode #{i + 1}'
        metadata = {
            'current': i,
            'total': episodes,
            'status': episode_nr
        }
        self.update_state(state='PROGRESS', meta=metadata)

        ob = env.reset()
        print(episode_nr)
        while True:
            metadata['status'] = episode_nr + f'; FPS: {env.clock.get_fps()}'
            self.update_state(state='PROGRESS', meta=metadata)
            env.render(render_mode)

            # action_n = agent.act(ob, reward, done) # should be some function to choose action
            action_n = [1, 1]  # temp
            obs_n, reward_n, done_n, _ = env.step(action_n)

            if all(done_n):
                break

    env.close()
    return {'time': round(time.time() - start, 2)}


@app.route('/status/<task_id>')
def get_task_status(task_id):
    task = train.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending... Why tho'
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'result': task.result,
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', 'Whaaat?'),
        }
    else:
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # exception
        }

    return jsonify(response)


@ app.route('/run', methods=['POST'])
def run_async_task():
    tasks = list()
    for _ in range(multiprocessing.cpu_count()):
        task = train.apply_async()
        tasks.append(task.id)

    return {'task_ids': tasks}, 202


@ app.route('/')
def hello_world():
    return render_template('homepage.html')


if __name__ == '__main__':
    celery.control.purge()
    app.run(debug=True, host='0.0.0.0')
