
from broker.broker import Broker
from subscriber.catan_player import CatanPlayer
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.catan_utils import CatanPygameUI, RED, BLUE, GREEN, YELLOW
import base64
import io

class CatanBroker(Broker):

    def __init__(self, config, use_multi_thread=False):
        super().__init__()
        self.use_multi_thread = use_multi_thread

        self.players = []
        for player_config in config['players']:
            player = CatanPlayer(player_config)
            self.players.append(player)

        for player in self.players:
            self.register(player, "place_initial_settlements")
            self.register(player, "place_initial_roads")
            self.register(player, "production_phase")
            self.register(player, "roll_dice")
            self.register(player, "trade_n_build_phase")
            self.register(player, "trade")
            self.register(player, "response_to_trade")
            self.register(player, "maritime_trade")
            self.register(player, "build_road")
            self.register(player, "build_settlement")
            self.register(player, "build_city")
            self.register(player, "buy_development_card")
            self.register(player, "play_development_card")
            self.register(player, "move_robber")
            
    
    def generate_observation_image(self, observation):
                
        import pygame

        pygame.init()
        screen = pygame.Surface((800, 600))  # Create a surface instead of a window

        current_player_index = 0
        self.player_colors = [RED, BLUE, GREEN]
        self.player_names = ["red", "green", "blue"]
        player_color = self.player_colors[current_player_index]
        player_name = self.player_names[current_player_index]
        scores = observation['scores']
        ui = CatanPygameUI(screen, observation, player_name, player_color)

        ui.draw(scores)
        # Your existing drawing code here, e.g.:
        # screen.fill((255, 255, 255))
        # draw hexagons, settlements, roads, etc.
        # Example:
        # for hex in catan_map.hexagons.values():
        #     pygame.draw.polygon(screen, hex.color, hex.points)
        import pygame.image

        # Save the surface as an image file
        pygame.image.save(screen, 'resources/catan.png')

        # Read the image file
        with open('resources/catan.png', 'rb') as image_file:
            image_data = image_file.read()

        # Convert the image data to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        pygame.quit()
        
        return image_base64

    def publish(self, topic, image, observation):
            
        print(f"\033[91m send message [{topic}] \033[0m")
        responses = []

        def notify_subscriber(subscriber):
            # Generate image from observation
            observation_image_base64 = None
            
            # observation_image_base64 = self.generate_observation_image(observation) if "dice" in topic else None
            filtered_observation = observation
            
            # if "dice" in topic:
                
            #     import matplotlib.pyplot as plt

            #     def show_image_base64(image_base64):
            #         image_data = base64.b64decode(image_base64)
            #         image = plt.imread(io.BytesIO(image_data), format='JPG')
            #         plt.imshow(image)
            #         plt.axis('off')
            #         plt.show()

            #     show_image_base64(observation_image_base64)
                
            return subscriber.notify(topic, observation_image_base64, filtered_observation)

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
    

    def register_by_name(self, name, topic):
        for player in self.players:
            if player.name == name:
                self.register(player, topic)
                

    def unregister_by_name(self, name, topic):
        for player in self.players:
            if player.name == name:
                self.unregister(player, topic)