from broker.broker import Broker
from subscriber.werewolf_player import WerewolfGamePlayer
from subscriber.werewolf_human_ui import WerewolfUI
from subscriber.werewolf_random_player import WerewolfRandomPlayer
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy

import matplotlib.pyplot as plt
import io
import base64

class WerewolfGameBroker(Broker):
    
    def __init__(self, config, use_multi_thread=False):
        super().__init__()
        # self.subscribers = {}
        
        self.use_multi_thread = use_multi_thread
        
        self.players = []
        for player_config in config['players']:
            if player_config['strategy'] == 'human':
                player = WerewolfUI(player_config)
            elif player_config['strategy'] == 'random':
                player = WerewolfRandomPlayer(player_config)
            else:
                player = WerewolfGamePlayer(player_config)
            self.players.append(player)

        for player in self.players:
            self.register(player, "start")
            self.register(player, "day_discuss")
            self.register(player, "day_vote")

        for player in self.players:
            if player.role == "werewolf":
                self.register(player, "wolf_action")
            elif player.role == "seer":
                self.register(player, "seer_action")
            elif player.role == "witch":
                self.register(player, "witch_heal")
                self.register(player, "witch_poison")
            elif player.role == "hunter":
                self.register(player, "hunter_action")

    def filter_observation(self, subscriber, observation):
        filtered_observation = copy.deepcopy(observation)
        filtered_observation["log"] = self.filter_log_for_role(subscriber, observation["log"])
        
        if subscriber.role == "werewolf":
            return self.filter_observation_for_werewolf(subscriber, filtered_observation)
        elif subscriber.role == "seer":
            return self.filter_observation_for_seer(subscriber, filtered_observation)
        elif subscriber.role == "witch":
            return self.filter_observation_for_witch(subscriber, filtered_observation)
        elif subscriber.role == "hunter":
            return self.filter_observation_for_hunter(subscriber, filtered_observation)
        else:
            return self.filter_observation_for_villager(subscriber, filtered_observation)

    def filter_log_for_role(self, subscriber, log):
        role = subscriber.role
        filtered_log = []

        for entry in log:
            if role == "werewolf":
                if entry["state"] in ["wolf_action", "wolf_win", "good_win", "start", "night", "end"]:
                    filtered_log.append(entry)
                else:
                    filtered_entry = entry.copy()
                    filtered_entry["responses"] = "unknown"
                    filtered_log.append(entry)
                
            elif role == "seer":
                if entry["state"] in ["seer_action", "good_win", "wolf_win", "start", "night", "end"]:
                    filtered_log.append(entry)
                else:
                    filtered_entry = {"state": entry["state"]}
                    filtered_log.append(filtered_entry)
                
            elif role == "witch":
                if entry["state"] in ["witch_heal", "witch_poison", "good_win", "wolf_win", "start", "night", "end"]:
                    filtered_log.append(entry)
                else:
                    filtered_entry = {"state": entry["state"]}
                    filtered_log.append(filtered_entry)
                
            elif role == "hunter":
                if entry["state"] in ["hunter_action", "good_win", "wolf_win", "start", "night", "end"]:
                    filtered_log.append(entry)
                else:
                    filtered_entry = {"state": entry["state"]}
                    filtered_log.append(filtered_entry)
                
            # else:  # Villagers and other roles
            if entry["state"] in ["day", "day_vote", "day_discuss", "day_last_words", "good_win", "wolf_win", "start", "night", "end"]:
                filtered_log.append(entry)
                
                
        return filtered_log

    def filter_observation_for_villager(self, subscriber, observation):
        filtered_observation = copy.deepcopy(observation)
        # Villagers can see everything except the roles of other players
        for player in filtered_observation["players"]:
            if player["name"] != subscriber.name:
                player["role"] = "unknown"  # Hide roles of other players
        return filtered_observation

    def filter_observation_for_seer(self, subscriber, observation):
        filtered_observation = copy.deepcopy(observation)
        # Seer can see the roles they have checked but not the roles of other players
        for player in filtered_observation["players"]:
            if player["name"] != subscriber.name and player["role"] != "seer":
                player["role"] = "unknown"  # Hide roles of other players unless they have been checked by the Seer
        # If seer has checked anyone, show those checks (assuming this info is logged)
        # This can be enhanced if you keep track of checks somewhere in the observation
        return filtered_observation

    def filter_observation_for_witch(self, subscriber, observation):
        filtered_observation = copy.deepcopy(observation)
        # Witch can see who was targeted at night and whether they used their heal or poison
        filtered_observation["werewolf_victim"] = observation.get("werewolf_victim", "error")
        filtered_observation["witch_used_heal"] = observation.get("witch_used_heal", False)
        filtered_observation["witch_used_poison"] = observation.get("witch_used_poison", False)
        # Hide roles of other players unless the witch
        for player in filtered_observation["players"]:
            if player["name"] != subscriber.name:
                player["role"] = "unknown"  # Hide roles of other players
        return filtered_observation

    def filter_observation_for_werewolf(self, subscriber, observation):
        filtered_observation = copy.deepcopy(observation)
        # Werewolves can see each other and the night victim but not the roles of other non-werewolves
        for player in filtered_observation["players"]:
            if player["role"] != "werewolf" and player["name"] != subscriber.name:
                player["role"] = "unknown"  # Hide roles of non-werewolves
        return filtered_observation

    def filter_observation_for_hunter(self, subscriber, observation):
        filtered_observation = copy.deepcopy(observation)
        # Hunter can see everything except the roles of other players
        for player in filtered_observation["players"]:
            if player["name"] != subscriber.name:
                player["role"] = "unknown"  # Hide roles of other players
        # Optionally, you could add specific insights for the Hunter if needed
        return filtered_observation


    def generate_observation_image(self, filtered_observation):
        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(12, 8))

        # Hide the axes
        ax.axis('off')

        # Create text from filtered observation
        text = ""
        for key, value in filtered_observation.items():
            if "current_state" not in key:
                continue
            if isinstance(value, dict):
                text += f"{key}:\n"
                for sub_key, sub_value in value.items():
                    text += f"  {sub_key}: {sub_value}\n"
            elif isinstance(value, list):
                text += f"{key}:\n"
                for item in value:
                    text += f"  {item}\n"
            else:
                text += f"{key}: {value}\n"

        # Draw text on the figure
        ax.text(0.5, 0.5, text, va='center', ha='center', wrap=True, fontsize=10)

        # Save the plot to a BytesIO object
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)

        # Encode the BytesIO object to base64
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')

        return img_base64

        
    
    def publish(self, topic, message, observation):
        if topic in self.subscribers:
            print(f"\033[91msend message [{topic}]: {message}\033[0m")
            responses = []

            def notify_subscriber(subscriber):
                filtered_observation = self.filter_observation(subscriber, observation)
                # observation_image = self.generate_observation_image(filtered_observation)
                observation_image = None
                return subscriber.notify(topic, message, observation_image, filtered_observation)

            alive_players = [p['name'] for p in observation['players'] if p['status'] == 'alive']
            topic_subscribers = [s for s in self.subscribers[topic] if s.name in alive_players]
            if len(topic_subscribers) == 0:
                topic_subscribers = self.subscribers[topic][:1]

            if self.use_multi_thread and topic != 'day_discuss':
                with ThreadPoolExecutor(max_workers=len(topic_subscribers)) as executor:
                    futures = {executor.submit(notify_subscriber, subscriber): subscriber for subscriber in topic_subscribers}
                    
                    for future in as_completed(futures):
                        response = future.result()
                        if response is not None:
                            responses.append(response)
            else:
                for subscriber in topic_subscribers:
                    response = notify_subscriber(subscriber)
                    if topic == 'day_discuss':
                        for p in topic_subscribers:
                            p.context.append(f'{subscriber.name}: {response["answer"]["discuss"]}')
                    if response is not None:
                        responses.append(response)
                        
            return responses
        return []

    def unregister_all_topics_by_name(self, name):
        for topic in self.subscribers.keys():
            for subscriber in self.subscribers[topic]:
                if subscriber.name == name:
                    self.unregister(subscriber, topic)

    def register_one_topic_by_name(self, name, topic):
        for player in self.players:
            if player.name == name:
                self.register(player, topic)


    def register_by_name(self, name, topic):
        for player in self.players:
            if player.name == name:
                self.register(player, topic)
                
    def unregister_by_name(self, name, topic):
        for player in self.players:
            if player.name == name:
                self.unregister(player, topic)

    
    
    