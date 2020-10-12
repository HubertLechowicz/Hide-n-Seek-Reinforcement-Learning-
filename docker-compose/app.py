from flask import Flask, render_template, jsonify, request
from celery import Celery
from celery.result import AsyncResult

import time
import random
import datetime
from pytz import timezone
import copy
from PIL import Image as img
from pathlib import Path
import shutil

import gym
import game_env.hidenseek_gym
from gym import wrappers
from game_env.hidenseek_gym import wrappers as multi_wrappers
from game_env.hidenseek_gym.config import config as default_config

app = Flask(__name__)
celery = Celery(broker='redis://redis:6379/0', backend='redis://redis:6379/0')


@celery.task(name='sleep.quartet', bind=True)
def train(self, core_id, config_data, start_date):
    cfg = copy.deepcopy(default_config)
    if '.bmp' not in config_data['map_path']:
        config_data['map_path'] += '.bmp'

    cfg['GAME']['MAP'] = '/opt/app/' + config_data['map_path']
    cfg['GAME']['FPS'] = config_data['fps']
    cfg['GAME']['DURATION'] = config_data['duration']
    episodes = int(config_data['episodes'])

    cfg['AGENT_HIDING'] = {
        'SPEED_RATIO': config_data['hiding-speed'],
        'SPEED_ROTATE_RATIO': config_data['hiding-speed-rotate'],
        'WALL_ACTION_TIMEOUT': config_data['hiding-wall-timeout'],
        'WALLS_MAX': config_data['hiding-walls'],
    }

    cfg['AGENT_SEEKER'] = {
        'SPEED_RATIO': config_data['seeker-speed'],
        'SPEED_ROTATE_RATIO': config_data['seeker-speed-rotate'],
        'WALL_ACTION_TIMEOUT': config_data['seeker-wall-timeout'],
    }

    start = time.time()

    render_mode = 'rgb_array'
    env = gym.make('hidenseek-v0', config=cfg)
    env.seed(0)
    monitor_folder = 'monitor/' + start_date + '/core-' + str(core_id)
    env = multi_wrappers.MultiMonitor(env, monitor_folder, force=True)
    done = False

    for i in range(1, episodes + 1):
        metadata = {
            'core_id': core_id,
            'current': i,
            'total': episodes,
            'episode_iter': config_data['duration'],
            'status': {'fps': None, 'iteration': 0, 'iteration_percentage': 0, 'time_elapsed': round(time.time() - start), 'image_path': None, 'eta': None},
        }
        self.update_state(state='PROGRESS', meta=metadata)

        env.reset()
        env.render(render_mode)
        while True:
            metadata['status'] = {
                'fps': env.clock.get_fps(),
                'iteration': int(config_data['duration']) - env.duration,
                'iteration_percentage': round(((int(config_data['duration']) - env.duration) / int(config_data['duration'])) * 100, 2),
                'time_elapsed': round(time.time() - start),
                'eta': round((env.duration / env.clock.get_fps()) + int(config_data['duration']) / env.clock.get_fps() * (episodes - i)) if env.clock.get_fps() else None,
            }

            # action_n = agent.act(ob, reward, done) # should be some function to choose action
            action_n = [1, 1]  # temp
            obs_n, reward_n, done, _ = env.step(action_n)

            step_img_path = '/opt/app/static/images/' + \
                start_date + '/core-' + str(core_id) + \
                '/frame-' + str(env.duration + 1) + '.jpg'
            step_img = env.render(render_mode)
            step_img = img.fromarray(step_img, mode='RGB')
            step_img.save(step_img_path)
            metadata['status']['image_path'] = step_img_path[8:]

            self.update_state(state='PROGRESS', meta=metadata)

            if done:
                break

    env.close()
    rm_path = Path('/opt/app/static/images/' +
                   start_date + '/core-' + str(core_id))
    shutil.rmtree(rm_path)

    return {
        'core_id': core_id,
        'time_elapsed': round(time.time() - start),
    }


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
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', {}),
            'episode_iter': task.info.get('episode_iter', 0),
            'config': task.info.get('config', {}),
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

    tz_local = timezone('Europe/Warsaw')
    now = datetime.datetime.now(tz=tz_local)
    start_date = datetime.datetime.strftime(now, "%Y-%m-%dT%H-%M-%SZ")

    tasks = list()
    for i in range(int(data['cpus'])):
        Path('/opt/app/static/images/' + start_date + '/core-' +
             str(i)).mkdir(parents=True, exist_ok=True)
        task = train.apply_async((i, data['configs'][i], start_date))
        tasks.append(task.id)

    return {'task_ids': tasks, 'start_date': start_date}, 202


@ app.route('/')
def homepage():
    return render_template('homepage.html')


if __name__ == '__main__':
    celery.control.purge()
    app.run(debug=True, host='0.0.0.0')
