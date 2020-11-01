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
import statistics

import gym
import game_env.hidenseek_gym
from gym import wrappers
from game_env.hidenseek_gym import wrappers as multi_wrappers
from game_env.hidenseek_gym.config import config as default_config
from game_env.hidenseek_gym.controllable import Seeker, Hiding
from game_env.hidenseek_gym.supportive import Point, Collision, MapGenerator
from game_env.hidenseek_gym.fixed import Wall
from helpers import Helpers

app = Flask(__name__)
celery = Celery(broker='redis://redis:6379/0', backend='redis://redis:6379/0')


@celery.task(name='train.core', bind=True)
def train(self, core_id, config_data, start_date):
    cfg = Helpers.prepare_config(config_data)

    start = time.time()

    map_bmp = MapGenerator.open_bmp(cfg['game']['map'])
    all_objects = MapGenerator.get_objects_coordinates(
        map_bmp, MapGenerator.get_predefined_palette())

    walls, seeker, hider, width, height = Helpers.generate_map(
        all_objects, map_bmp, cfg)

    map_bmp.close()  # memory management

    render_mode = 'rgb_array'
    env = gym.make(
        'hidenseek-v1',
        config=cfg,
        width=width,
        height=height,
        seeker=seeker,
        hiding=hider,
        walls=walls
    )
    env.seed(0)
    monitor_folder = 'monitor/' + start_date + '/core-' + str(core_id)
    env = multi_wrappers.MultiMonitor(
        env,
        monitor_folder,
        force=True,
        config=cfg
    )
    step_img_path = '/opt/app/static/images/core-' + \
        str(core_id) + '/last_frame.jpg'

    fps_batch = []

    for i in range(cfg['game']['episodes']):
        metadata = {
            'core_id': core_id,
            'current': i + 1,
            'total': cfg['game']['episodes'],
            'episode_iter': cfg['game']['duration'],
            'status': {'fps': None, 'iteration': 0, 'iteration_percentage': 0, 'time_elapsed': round(time.time() - start), 'image_path': step_img_path, 'eta': None, 'rewards': [0, 0]},
        }
        self.update_state(state='PROGRESS', meta=metadata)

        obs_n = env.reset()
        reward_n = [0, 0]
        rewards_ep = [0, 0]
        done = [False, None]
        fps_episode = []
        while True:
            rewards_ep = [rewards_ep[0] + reward_n[0],
                          rewards_ep[1] + reward_n[1]]
            metadata['status'] = {
                'fps': env.clock.get_fps(),
                'iteration': int(cfg['game']['duration']) - env.duration,
                'iteration_percentage': round(((int(cfg['game']['duration']) - env.duration) / int(cfg['game']['duration'])) * 100, 2),
                'time_elapsed': round(time.time() - start),
                'eta': round((env.duration / env.clock.get_fps()) + int(cfg['game']['duration']) / env.clock.get_fps() * cfg['game']['episodes']) if env.clock.get_fps() else None,
                'image_path': step_img_path[8:],
                'rewards': rewards_ep,
            }
            fps_episode.append(env.clock.get_fps())

            action_n = [seeker.act(obs_n[0], reward_n[0], done[0], env.action_space),
                        hider.act(obs_n[1], reward_n[1], done[0], env.action_space)]
            obs_n, reward_n, done, _ = env.step(action_n)

            # 1% chance to get new frame update if monitoring enabled
            if cfg['video']['monitoring'] and random.random() < .01:
                step_img = env.render(render_mode)
                step_img = img.fromarray(step_img, mode='RGB')
                step_img.save(step_img_path)
                step_img.close()

            self.update_state(state='PROGRESS', meta=metadata)

            if done[0]:
                break

        fps_batch.append(statistics.fmean(fps_episode))

    env.close()
    rm_path = Path('/opt/app/static/images/core-' + str(core_id))
    shutil.rmtree(rm_path)

    return {
        'core_id': core_id,
        'time_elapsed': round(time.time() - start),
        'fps_peak': round(max(fps_batch)),
        'fps_lower': round(min(fps_batch)),
        'fps_mean': round(statistics.fmean(fps_batch)),
        'fps_median': round(statistics.median(fps_batch)),
        'fps_quantiles': [round(quantile) for quantile in statistics.quantiles(fps_batch)],
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
        Path('/opt/app/static/images/core-' +
             str(i)).mkdir(parents=True, exist_ok=True)
        task = train.apply_async((i, data['configs'][i], start_date))
        tasks.append(task.id)

    return {'task_ids': tasks, 'start_date': start_date}, 202


@ app.route('/')
def homepage():
    return render_template('homepage.html', cfg=default_config)


if __name__ == '__main__':
    celery.control.purge()
    app.run(debug=True, host='0.0.0.0')
