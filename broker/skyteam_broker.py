### ./broker/skyteam_broker.py ###
from broker.broker import Broker
from subscriber.skyteam_player import SkyTeamPlayer
from subscriber.skyteam_naive_player import SkyTeamNaivePlayer
from subscriber.skyteam_human_ui import SkyTeamUI
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO

class SkyTeamGameBroker(Broker):
    
    def __init__(self, config, use_multi_thread=False):
        super().__init__()
        self.use_multi_thread = use_multi_thread

        players = []
        for player_config in config['players']:
            
            if player_config['strategy'] == 'human':
                player = SkyTeamUI(player_config)
            elif player_config['strategy'] == 'naive':
                player = SkyTeamNaivePlayer(player_config)
            else:
                player = SkyTeamPlayer(player_config)
            players.append(player)

        for player in players:
            self.register(player, "start")
            self.register(player, "end")
            self.register(player, "round_start")
            self.register(player, "discuss")
            self.register(player, "reroll_dice")
            
            if player.role == "pilot":
                self.register(player, "pilot_action") 
            elif player.role == "copilot":
                self.register(player, "copilot_action")
    
    def filter_observation(self, subscriber, observation):
        filtered_observation = observation.copy()

        if subscriber.role in ["pilot"]:
            filtered_observation["current_round_dices"] = {
                "pilot": observation["current_round_dices"]["pilot"],
            }
        elif subscriber.role in ["copilot"]:
            filtered_observation["current_round_dices"] = {
                "copilot": observation["current_round_dices"]["copilot"],
            }
        
        return filtered_observation

    def generate_observation_image(self, observation):
        fig, axs = plt.subplots(2, 1, figsize=(10, 8))
        
        # Create table data for tracks
        columns = ['Step 1', 'Step 2', 'Step 3', 'Step 4', 'Step 5', 'Step 6', 'Step 7']
        approach_track = observation["approach_track"]
        altitude_track = observation["altitude_track"]
        
        track_data = [
            approach_track,
            altitude_track
        ]
        track_row_labels = ['Approach Track', 'Altitude Track']
        
        # Create table for tracks
        axs[0].axis('tight')
        axs[0].axis('off')
        track_table = axs[0].table(cellText=track_data, colLabels=columns, rowLabels=track_row_labels, loc='center', cellLoc='center')
        track_table.auto_set_font_size(False)
        track_table.set_fontsize(12)
        # track_table.scale(1.2, 1.2)
        
        # Create table data for dices
        dice_columns = ['Dice 1', 'Dice 2', 'Dice 3', 'Dice 4']
        pilot_dices = observation["current_round_dices"]["pilot"].copy()
        copilot_dices = observation["current_round_dices"]["copilot"].copy()
        
        # Ensure dice data has at least empty strings for each dice slot
        max_dice_count = max(len(pilot_dices), len(copilot_dices), 4)
        pilot_dices += [''] * (max_dice_count - len(pilot_dices))
        copilot_dices += [''] * (max_dice_count - len(copilot_dices))
        
        dice_data = [
            pilot_dices,
            copilot_dices
        ]
        dice_row_labels = ['Pilot Dices', 'Copilot Dices']
        
        # Create table for dices
        axs[1].axis('tight')
        axs[1].axis('off')
        dice_table = axs[1].table(cellText=dice_data, colLabels=dice_columns, rowLabels=dice_row_labels, loc='center', cellLoc='center')
        dice_table.auto_set_font_size(False)
        dice_table.set_fontsize(12)
        # dice_table.scale(1.2, 1.2)
        
        # Save plot to a BytesIO object
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # Convert to base64
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        plt.close(fig)
        
        return image_base64
    
    def publish(self, topic, message, observation):
        if topic in self.subscribers:
            print(f"\033[91m send message [{topic}]: {message}\033[0m")
            responses = []

            def notify_subscriber(subscriber):
                filtered_observation = self.filter_observation(subscriber, observation)
                # image_base64 = self.generate_observation_image(observation)
                image_base64 = None
                return subscriber.notify(topic, message, image_base64, filtered_observation)

            if self.use_multi_thread:
                with ThreadPoolExecutor(max_workers=len(self.subscribers[topic])) as executor:
                    futures = {executor.submit(notify_subscriber, subscriber): subscriber for subscriber in self.subscribers[topic]}
                    
                    for future in as_completed(futures):
                        response = future.result()
                        if response is not None:
                            responses.append(response)
            else:
                for subscriber in self.subscribers[topic]:
                    response = notify_subscriber(subscriber)
                    if response is not None:
                        responses.append(response)

            return responses
        return []
