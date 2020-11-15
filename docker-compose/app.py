from flask import Flask, render_template, jsonify, request
from celery import Celery
from celery.result import AsyncResult

import time
import datetime
from pytz import timezone
from pathlib import Path
import statistics

import game_env.hidenseek_gym
from game_env.hidenseek_gym.config import config as default_config
from rl import A2C
from helpers import Helpers

app = Flask(__name__)
celery = Celery(broker='redis://redis:6379/0', backend='redis://redis:6379/0')
celery.conf.broker_transport_options = {"visibility_timeout": 3600 * 24 * 360} # 1h * 24 * 360 = 360d


@celery.task(name='train.core', bind=True)
def train(self, core_id, config_data, start_date):
    start = time.time()
    cfg = Helpers.prepare_config(config_data)

    walls, seeker, hiding, width, height = Helpers.prepare_map(cfg)

    env, step_img_path, fps_batch, render_mode, wins_l = Helpers.create_env(
        config=cfg,
        width=width,
        height=height,
        walls=walls,
        seeker=seeker,
        hiding=hiding,
        start_date=start_date,
        core_id=core_id,
    )

    AGENTS = 2
    algorithm = Helpers.pick_algorithm(cfg, env=env, agents=AGENTS)
    algorithm.prepare_model()

    for i in range(cfg['game']['episodes']):
        algorithm.before_episode()
        metadata = Helpers.update_celery_metadata(
            core_id=core_id,
            curr=i + 1,
            total=cfg['game']['episodes'],
            ep_iter=cfg['game']['duration'],
            fps=None,
            itera=0,
            iter_perc=0,
            time_elap=round(time.time() - start),
            img_path=step_img_path,
            eta=None,
            rewards=[0, 0],
            wins=[0, 0],
            wins_moving=[0, 0],
        )
        self.update_state(state='PROGRESS', meta=metadata)

        obs_n, reward_n, rewards_ep, done, fps_episode = Helpers.new_ep(env)

        while True:
            rewards_ep = [rewards_ep[0] + reward_n[0],
                          rewards_ep[1] + reward_n[1]]
            metadata['status'] = Helpers.update_metadata_status(
                fps=env.clock.get_fps(),
                itera=int(cfg['game']['duration']) - env.duration,
                iter_perc=round(
                    ((int(cfg['game']['duration']) - env.duration) / int(cfg['game']['duration'])) * 100, 2),
                time_elap=round(time.time() - start),
                eta=round((env.duration / env.clock.get_fps()) + int(cfg['game']['duration']) / env.clock.get_fps(
                ) * cfg['game']['episodes']) if env.clock.get_fps() else None,
                img_path=step_img_path[8:],
                rewards=rewards_ep,
                wins=[sum(w) for w in wins_l],
                wins_moving=[sum(w[-10:]) for w in wins_l],
            )

            fps_episode.append(env.clock.get_fps())

            algorithm.before_action(obs_n=obs_n)

            action_n = algorithm.take_action(obs_n=obs_n)

            algorithm.before_step(action_n=action_n)
            obs_n, reward_n, done, _ = env.step(action_n)
            algorithm.after_step(reward_n=reward_n,done=done)

            Helpers.update_img_status(
                env, cfg['video']['monitoring'], step_img_path, render_mode)
            self.update_state(state='PROGRESS', meta=metadata)

            if done[0]:
                algorithm.handle_gameover(
                    obs_n=obs_n,
                    reward_n=reward_n,
                    ep_length=int(cfg['game']['duration']) - env.duration,
                )
                Helpers.handle_gameover(done[1], wins_l)
                break

        algorithm.after_episode()

        fps_batch.append(statistics.fmean(fps_episode))

    algorithm.before_cleanup()
    Helpers.cleanup(env, core_id)

    return Helpers.get_celery_success(
        core_id=core_id,
        time_elap=round(time.time() - start, 4),
        fps_batch=fps_batch,
        wins=[sum(w) for w in wins_l],
    )


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
