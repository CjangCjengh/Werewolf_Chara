import argparse
import yaml
import time
import os
import avalon, azul, skyteam, hanabi, codenames, carcassonne, werewolf, landlord, codenames

import socket

from flask import Flask, render_template, jsonify
import subprocess
import threading
import multiprocessing
# multiprocessing.set_start_method("spawn")

app = Flask(__name__, template_folder='subscriber/templates', static_folder='static')


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def wait_for_port(port, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(1)
    return False


@app.route('/')
def index():
    return render_template('index.html')


def run_game(config):
    subprocess.run(['python', 'main.py', config])


@app.route('/launch/<game>')
def launch_game(game):
    # def run_game(config):
    #     subprocess.run(['python', 'main.py', config])

    config_map = {
        'avalon': ('configs/avalon/human(merlin)-random.yaml', 5001),
        'azul': ('configs/azul/human-heuristic.yaml', 5002),
        'codenames': ('configs/codenames/human(redmaster)-random.yaml', 5003),
        'hanabi': ('configs/hanabi/human-random.yaml', 5004),
        'skyteam': ('configs/skyteam/human(pilot)-random.yaml', 5005),
        'werewolf': ('configs/werewolf/human(witch)-deepseek.yaml', 5006),
        'landlord': ('configs/landlord/landlord-rd-hm.yaml', 5007)
    }
    config, port = config_map.get(game, (None, None))
    if config:
        if is_port_in_use(port):
            return jsonify(success=False, message=f'Port {port} is already in use.')

        p = multiprocessing.Process(target=run_game, args=(config,))
        p.start()

        if wait_for_port(port):
            return jsonify(success=True, url=f'http://127.0.0.1:{port}')
        else:
            return jsonify(success=False, message='Failed to start game in time')

    else:
        return jsonify(success=False, message='Invalid game.')


if __name__ == '__main__':
    app.run(port=5000, debug=True)

# def main():

#     parser = argparse.ArgumentParser()
#     parser.add_argument('configs', help='game config file')

#     args = parser.parse_args()
#     config_file = args.configs

#     with open(config_file, 'r', encoding='utf-8') as file:
#         config = yaml.safe_load(file)

#     game_name = config.get('game').get('name')

#     config.update({'config_file_path': config_file})


#     t = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
#     log_directory = os.path.join(f"logs/{game_name}", t)
#     os.makedirs(log_directory, exist_ok=True)

#     config.update({'log_directory': log_directory})


#     if game_name == 'avalon':
#         avalon.avalon(config)
#     elif game_name == 'azul':
#         azul.azul(config)
#     elif game_name == 'skyteam':
#         skyteam.skyteam(config)
#     elif game_name == 'hanabi':
#         hanabi.hanabi(config)
#     elif game_name == 'codenames':
#         codenames.codenames(config)
#     elif game_name == 'catan':
#         catan.catan(config)
#     elif game_name == 'carcassonne':
#         carcassonne.carcassonne(config)
#     elif game_name == 'werewolf':
#         werewolf.werewolf(config)
#     elif game_name == 'landlord':
#         landlord.landlord(config)


# if __name__ == "__main__":
#     main()
