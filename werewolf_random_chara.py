import time
import os
import werewolf
import random
from multiprocessing import Process


def single_game():
    name_list = ['ayaka', 'baizhantang', 'duanyu', 'dumbledore', 'guofurong', 'harry', 'haruhi', 'hermione', 'hutao', 'jiumozhi', 'linghuchong', 'liyunlong', 'luna', 'malfoy', 'mcgonagall', 'murongfu', 'normal', 'penny', 'qiaofeng', 'raidenshogun', 'raj', 'ron', 'sheldon', 'snape', 'tangshiye', 'tongxiangyu', 'wanderer', 'wangduoyu', 'wangyuyan', 'weixiaobao', 'xiaofeng', 'xinghui', 'xuzhu', 'yuebuqun', 'yuqian', 'zhongli']
    roles = ['werewolf'] * 3 + ['seer', 'witch', 'hunter'] + ['villager'] * 3
    random.shuffle(roles)
    selected_names = random.sample(name_list, 9)

    players = [{'name': name.capitalize(), 'role': role, 'strategy': 'character', 'character': name, 'model': 'gpt-4o-mini'}
            for name, role in zip(selected_names, roles)]

    config = {'game': {'name': 'werewolf'}, 'players': players}

    game_name = config.get('game').get('name')

    t = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    log_directory = os.path.join(f"logs/{game_name}", t)
    os.makedirs(log_directory, exist_ok=True)
    
    config.update({'log_directory': log_directory}) 

    werewolf.werewolf(config)

def monitor_game():
    process = Process(target=single_game)
    process.start()
    process.join(timeout=300)
    if process.is_alive():
        process.terminate()
        process.join()
    time.sleep(5)


if __name__ == "__main__":
    while True:
        try:
            monitor_game()
        except:
            time.sleep(60)
