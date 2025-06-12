from broker.broker import Broker
from subscriber.hanabi_player import HanabiPlayer
from subscriber.hanabi_human_ui import HanabiUI
from subscriber.hanabi_random_player import HanabiRandomPlayer
from subscriber.hanabi_naive_player import HanabiNaivePlayer
from concurrent.futures import ThreadPoolExecutor, as_completed

class HanabiGameBroker(Broker):
    
    def __init__(self, config, use_multi_thread=False):
        super().__init__()
        self.use_multi_thread = use_multi_thread

        players = []
        
        for player_config in config['players']:
            
            if player_config['strategy'] == 'human':
                
                player = HanabiUI(player_config)
            elif player_config['strategy'] == 'naive':
                    
                player = HanabiNaivePlayer(player_config)
            
            elif player_config['strategy'] == 'random':
                player = HanabiRandomPlayer(player_config)
            else:
                player = HanabiPlayer(player_config)
                
            players.append(player)
            
        for player in players:
            self.register(player, "start")
            self.register(player, "end")
            
            if player.role == "player1":

                self.register(player, "p1_choose_action") 
                self.register(player, "p1_give_clue")
                self.register(player, "p1_discard_card")
                self.register(player, "p1_play_card")
                self.register(player, "p1_done")    
                
            elif player.role == "player2":
                
                self.register(player, "p2_choose_action")
                self.register(player, "p2_give_clue")
                self.register(player, "p2_discard_card")
                self.register(player, "p2_play_card")
                self.register(player, "p2_done")
                
    def filter_observation(self, subscriber, observation):
        filtered_observation = observation.copy()  # Create a copy to avoid modifying the original

        # Filter the players_hands
        filtered_players_hands = {}
        for player, hand in filtered_observation["players_hands"].items():
            if player == subscriber.role:
                # Replace the player's own hand with None values
                filtered_players_hands[player] = [(None, None) for _ in hand]
            else:
                # Keep other players' hands as is
                filtered_players_hands[player] = hand

        # Update the filtered observation with the new players_hands
        filtered_observation["players_hands"] = filtered_players_hands

        return filtered_observation
    
    def publish(self, topic, message, image, observation):
        if topic in self.subscribers:
            # import ipdb; ipdb.set_trace()
            print(f"\033[91m send message [{topic}]: {message}\033[0m") 
            responses = []

            def notify_subscriber(subscriber):
                filtered_observation = self.filter_observation(subscriber, observation)
                filtered_observation = observation
                return subscriber.notify(topic, message, image, filtered_observation)

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
