import multiprocessing
from flask import Flask, render_template, jsonify, request
from celery import Celery, group
from celery.result import AsyncResult
import time
import random
import datetime
from pytz import timezone

import gym
import game_env.hidenseek_gym
from gym import wrappers
from game_env.hidenseek_gym import wrappers as multi_wrappers

app = Flask(__name__)
celery = Celery(broker='redis://redis:6379/0', backend='redis://redis:6379/0')


@celery.task(name='sleep.quartet', bind=True)
def train(self, core_id, config_data):
    print(config_data)
    # config is in variable above, should create configparser Object to not mess with Game structure
    # {
    #     'episodes': '100',
    #     'map_path': 'b',
    #     'fps': '60',
    #     'duration': '1000',
    #     'seeker-speed': '1.00',
    #     'seeker-speed-rotate': '0.10',
    #     'seeker-wall-timeout': '100',
    #     'seeker-walls': '100',
    #     'hiding-speed': '1.00',
    #     'hiding-speed-rotate': '0.10',
    #     'hiding-wall-timeout': '100'
    # }
    start = time.time()

    episodes = 2  # should be from FORM
    render_mode = 'rgb_array'
    tz_local = timezone('Europe/Warsaw')
    env = gym.make('hidenseek-v0')
    env.seed(0)
    now = datetime.datetime.now(tz=tz_local)
    monitor_folder = 'monitor/' + \
        datetime.datetime.strftime(
            now, "%Y-%m-%dT%H-%M-%SZ") + '/core-' + str(core_id)
    env = multi_wrappers.MultiMonitor(env, monitor_folder, force=True)
    done = False

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
            obs_n, reward_n, done, _ = env.step(action_n)

            if done:
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


@ app.route('/train', methods=['POST'])
def start_training():
    data = request.json
    tasks = list()
    for i in range(int(data['cpus'])):
        task = train.apply_async((i, data['configs'][i]))
        tasks.append(task.id)

    return {'task_ids': tasks}, 202


@ app.route('/')
def hello_world():
    return render_template('homepage.html')


if __name__ == '__main__':
    celery.control.purge()
    app.run(debug=True, host='0.0.0.0')
