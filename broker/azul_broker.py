from broker.broker import Broker
from subscriber.azul_player import AzulPlayer
from subscriber.azul_human_ui import AzulUI
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import io
import base64
from PIL import Image

class AzulGameBroker(Broker):

    def __init__(self, config, use_multi_thread=False):
        super().__init__()
        self.use_multi_thread = use_multi_thread

        players = []
        for player_config in config['players']:
            if player_config['strategy'] == 'human':
                player = AzulUI(player_config)
            else:
                player = AzulPlayer(player_config)
            players.append(player)

        for player in players:
            self.register(player, "start")
            self.register(player, "round_start")
            self.register(player, "round_end")
            self.register(player, "end")

        self.register(players[0], "p1_turn")
        self.register(players[1], "p2_turn")

    def publish(self, topic, message, image, observation):
        if topic in self.subscribers:
            print(f"\033[91m send message [{topic}]: {message}\033[0m")
            responses = []

            def notify_subscriber(subscriber):
                # Generate image from observation
                observation_image = self.generate_observation_image(observation)
                # Convert image to base64
                observation_image_base64 = self.convert_image_to_base64(observation_image)
                filtered_observation = observation
                return subscriber.notify(topic, message, observation_image_base64, filtered_observation)

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

    def generate_observation_image(self, observation):
        """Generate an image from the observation data."""
        fig, axs = plt.subplots(1, 3, figsize=(15, 5))

        # Factory state visualization
        factory_state = observation["factory"]
        table_data = [["Factory", "Tiles"]]
        for i, subfactory in enumerate(factory_state["Factories"].values(), start=1):
            table_data.append([f"Factory {i}", ', '.join(subfactory)])
        table_data.append(["Table Center", ', '.join(factory_state["TableCenter"])])

        axs[0].axis('tight')
        axs[0].axis('off')
        table = axs[0].table(cellText=table_data, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.2)
        axs[0].set_title("Factory State")

        # Player boards visualization
        for idx, (player_key, player_board) in enumerate(observation["players_boards"].items()):
            ax = axs[idx + 1]

            # Pattern lines
            pattern_lines = player_board["pattern_lines"]
            for row in range(len(pattern_lines)):
                tiles = pattern_lines[row]
                for col in range(row + 1):
                    color = tiles[col] if col < len(tiles) else 'white'
                    rect = patches.Rectangle((col, 5 - row - 1), 1, 1, linewidth=1, edgecolor='black', facecolor=color)
                    ax.add_patch(rect)

            # Wall
            wall = player_board["wall"]
            for row in range(len(wall)):
                for col in range(len(wall[row])):
                    color = wall[row][col] if wall[row][col] != '' else 'white'
                    rect = patches.Rectangle((col + 6, 5 - row - 1), 1, 1, linewidth=1, edgecolor='purple', facecolor=color)
                    ax.add_patch(rect)

            # Floorline as a table
            floorline = player_board["floorline"]
            floorline_table_data = [floorline + [''] * (8 - len(floorline))]
            table = ax.table(cellText=floorline_table_data, cellLoc='center', loc='bottom', bbox=[0, -0.3, 1, 0.15])
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            for key, cell in table.get_celld().items():
                cell.set_linewidth(1)
                    
                tile_color = floorline_table_data[0][key[1]]
                if tile_color == 'ONE':
                    cell.set_facecolor('gray')
                elif tile_color == '':
                    cell.set_facecolor('white')
                else:
                    cell.set_facecolor(tile_color)
                cell.set_edgecolor('black')

            ax.set_xlim(0, 11)
            ax.set_ylim(-2, 5)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_title(f"{player_key} Board")

        fig.canvas.draw()
        width, height = fig.canvas.get_width_height()
        img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        img = img.reshape(height, width, 3)

        plt.close(fig)
        return img

    def convert_image_to_base64(self, img):
        """Convert a NumPy array image to a base64 string."""
        img_pil = Image.fromarray(img)
        buffered = io.BytesIO()
        img_pil.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
