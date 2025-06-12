from broker.broker import Broker
from concurrent.futures import ThreadPoolExecutor, as_completed
from subscriber.avalon_player import AvalonPlayer
from subscriber.avalon_human_ui import AvalonUI
from subscriber.avalon_random_player import AvalonRandomPlayer
from subscriber.subscriber import Subscriber
import matplotlib.pyplot as plt
import io
import base64


class AvalonGameBroker(Broker):
    
    def __init__(self, config, use_multi_thread=False):
        super().__init__()
        self.use_multi_thread = use_multi_thread
        
        self.players = []
        for player_config in config['players']:
            if player_config['strategy'] == 'human':
                player = AvalonUI(player_config)
            elif player_config['strategy'] == 'random':
                player = AvalonRandomPlayer(player_config)
            else:
                player = AvalonPlayer(player_config)
            self.players.append(player)

        for player in self.players:
            self.register(player, "start")
            self.register(player, "round_start")
            self.register(player, "vote")
            self.register(player, "round_end")
            self.register(player, "end")
            
            if player.role == "Assassin":
                self.register(player, "assassin")
    
    def filter_observation(self, subscriber, observation):
        filtered_observation = observation.copy()
        role = subscriber.role

        if role == "Merlin":
            filtered_observation['players_roles'] = {
                player.name: "evil" if player.role in ["Assassin", "Morgana", "Mordred", "Oberon"] else "Unknown"
                for player in self.players
            }
        elif role in ["Assassin", "Morgana", "Mordred"]:
            filtered_observation['players_roles'] = {
                player.name: "evil" if player.role in ["Assassin", "Morgana", "Mordred"] and player.role != "Oberon" else "Unknown"
                for player in self.players
            }
        elif role == "Percival":
            filtered_observation['players_roles'] = {
                player.name: "Merlin or Morgana" if player.role in ["Merlin", "Morgana"] else "Unknown"
                for player in self.players
            }
        else:
            filtered_observation['players_roles'] = {player.name: "Unknown" for player in self.players}
        
        return filtered_observation


    def generate_observation_image(self, observation):
        # Create a figure and axis
        fig, ax = plt.subplots()

        # Example: Plot the players and their roles
        player_names = observation['players_names']
        player_roles = observation.get('players_roles', ["Unknown"] * len(player_names))

        # Plot player roles
        for i, (name, role) in enumerate(zip(player_names, player_roles)):
            ax.text(0.1, 1 - i * 0.1, f"{name}: {role}", fontsize=12)

        # Hide the axes
        ax.axis('off')

        # Save the plot to a BytesIO object
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Convert the BytesIO object to a base64 string
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()

        return image_base64
    
    def publish(self, topic, message, image, observation):
        if topic in self.subscribers:
            print(f"\033[91m send message [{topic}]: {message}\033[0m")
            responses = []

            def notify_subscriber(subscriber):
                filtered_observation = self.filter_observation(subscriber, observation)
                # observation_image = self.generate_observation_image(filtered_observation) # disable for unimodal
                observation_image = None
                return subscriber.notify(topic, message, observation_image, filtered_observation)

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

    def register_by_name(self, name, topic):
        for player in self.players:
            if player.name == name:
                self.register(player, topic)
                
    def unregister_by_name(self, name, topic):
        for player in self.players:
            if player.name == name:
                self.unregister(player, topic)
