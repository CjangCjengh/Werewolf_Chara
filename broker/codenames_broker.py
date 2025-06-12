from broker.broker import Broker
from concurrent.futures import ThreadPoolExecutor, as_completed
from subscriber.codenames_player import CodenamesPlayer
from subscriber.codenames_human_ui import CodenamesUI
from subscriber.codenames_random_player import CodenamesRandomPlayer
from subscriber.codenames_naive_player import CodenamesNaivePlayer

class CodenamesGameBroker(Broker):
    
    def __init__(self, config, use_multi_thread=False):
        super().__init__()
        self.use_multi_thread = use_multi_thread
        
        self.players = []
        for player_config in config['players']:
            
            if player_config['strategy'] == 'human':
                player = CodenamesUI(player_config)
            elif player_config['strategy'] == 'naive':
                player = CodenamesNaivePlayer(player_config)
            elif player_config['strategy'] == 'random':
                player = CodenamesRandomPlayer(player_config)
            else:
                player = CodenamesPlayer(player_config)
            self.players.append(player)

        for player in self.players:
            self.register(player, "start")
            self.register(player, "end")
            
            if player.role == "red_spymaster":
                self.register(player, "red_spymaster_give_clue")
            elif player.role == "blue_spymaster":
                self.register(player, "blue_spymaster_give_clue")
            elif player.role == "red_operative":
                self.register(player, "red_operative_guess")
            elif player.role == "blue_operative":
                self.register(player, "blue_operative_guess")
    
    
    def filter_observation(self, subscriber, observation):
        # todo filter observation based on subscriber's role
        # if subscriber.role  is operative, only show the board words, do not show the assassin word, the neutral words, and the team words
            
        filtered_observation = observation.copy()

        if subscriber.role in ["red_operative", "blue_operative"]:
            # Remove sensitive information for operatives
            filtered_observation.pop("red_team_words", None)
            filtered_observation.pop("blue_team_words", None)
            filtered_observation.pop("assassin_word", None)
            filtered_observation.pop("neutral_words", None)

        return filtered_observation
    
    
    def publish(self, topic, message, observation):
        if topic in self.subscribers:
            
            print(f"\033[91m send message [{topic}]: {message}\033[0m") 
            responses = []

            def notify_subscriber(subscriber):
                # filtered_observation = self.filter_observation(subscriber, observation)
                observation_image = None
                filtered_observation = self.filter_observation(subscriber, observation)
                return subscriber.notify(topic, message, None, filtered_observation)

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
