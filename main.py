
import argparse
import yaml
import time
import os
import avalon, azul, skyteam, hanabi, codenames, carcassonne, werewolf, landlord, codenames, catan


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('configs', help='game config file')

    args = parser.parse_args()
    config_file = args.configs
    
    with open(config_file, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    game_name = config.get('game').get('name')
    
    config.update({'config_file_path': config_file})
    
    
    t = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    log_directory = os.path.join(f"logs/{game_name}", t)
    os.makedirs(log_directory, exist_ok=True)
    
    config.update({'log_directory': log_directory}) 
    

    if game_name == 'avalon':
        avalon.avalon(config)
    elif game_name == 'azul':
        azul.azul(config)
    elif game_name == 'skyteam':
        skyteam.skyteam(config)
    elif game_name == 'hanabi':
        hanabi.hanabi(config)
    elif game_name == 'codenames':
        codenames.codenames(config)
    elif game_name == 'catan':
        catan.catan(config)
    elif game_name == 'carcassonne':
        carcassonne.carcassonne(config)
    elif game_name == 'werewolf':
        werewolf.werewolf(config)
    elif game_name == 'landlord':
        landlord.landlord(config)
    
        

if __name__ == "__main__":
    main()
