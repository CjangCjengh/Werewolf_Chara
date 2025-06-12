import pygame
import math
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
NUM_PLAYERS = 3
WIDTH, HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
LIGHT_BLUE = (173, 216, 230)

# PLAYER_COLORS = [RED, GREEN, BLUE]

# Hexagon properties
HEX_RADIUS = 40
HEX_HEIGHT = 2 * HEX_RADIUS
HEX_WIDTH = math.sqrt(3) * HEX_RADIUS

# Calculate the screen center
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2
import math


# Define colors
WHITE = (255, 255, 255)
FOREST_COLOR = (34, 139, 34)
PASTURE_COLOR = (173, 255, 47)
GRAIN_COLOR = (218, 165, 32)
CLAY_COLOR = (139, 69, 19)
HILL_COLOR = (112, 128, 144)
DESERT_COLOR = (238, 221, 130)

class Hexagon:
    def __init__(self, q, r, s):
        self.q = q
        self.r = r
        self.s = s
        self.color = WHITE
        self.number = None

    def pixel_coordinates(self):
        x = HEX_WIDTH * (self.q + self.r / 2)
        y = HEX_HEIGHT * (3 / 4 * self.r)
        return CENTER_X + x, CENTER_Y + y

    def get_corners(self):
        x, y = self.pixel_coordinates()
        return [
            (x + HEX_RADIUS * math.cos(math.pi / 3 * i + math.pi / 6),
                y + HEX_RADIUS * math.sin(math.pi / 3 * i + math.pi / 6))
            for i in range(6)
        ]

    def get_edges(self):
        corners = self.get_corners()
        return [(corners[i], corners[(i + 1) % 6]) for i in range(6)]
    
    
class CatanMap:
    def __init__(self, radius):
        self.hexes = self.generate_hexagonal_grid(radius)
        self.settlements = []
        self.roads = []
        self.temp_road_start = None
        self.current_observation = {
            "hexagons": {},
            "settlements": {},
            "roads": {}
        }


        self.player_names = ["red", "green", "blue"]
        self.player_colors = [RED, GREEN, BLUE]
        # Store initial hexagon information in the observation dictionary
        for hex in self.hexes:
            self.current_observation["hexagons"][(hex.q, hex.r, hex.s)] = {
                "color": hex.color,
                "position": hex.pixel_coordinates(),
                "number": hex.number
            }

    class Hexagon:
        def __init__(self, q, r, s):
            self.q = q
            self.r = r
            self.s = s
            # TODO: Add terrain type
            self.color = WHITE # TODO change the color based on the terrain type
            self.number = None

        def pixel_coordinates(self):
            x = HEX_WIDTH * (self.q + self.r / 2)
            y = HEX_HEIGHT * (3 / 4 * self.r)
            return CENTER_X + x, CENTER_Y + y

        def get_corners(self):
            x, y = self.pixel_coordinates()
            return [
                (round(x + HEX_RADIUS * math.cos(math.pi / 3 * i + math.pi / 6), 2),
                round(y + HEX_RADIUS * math.sin(math.pi / 3 * i + math.pi / 6), 2))
                for i in range(6)
            ]

        def get_edges(self):
            corners = self.get_corners()
            return [(corners[i], corners[(i + 1) % 6]) for i in range(6)]


    def assign_terrains_to_hexes(self, hexes, terrains, numbers):
        for hexagon, terrain, number in zip(hexes, terrains, numbers):
            hexagon.terrain = terrain
            if terrain == "Forest":
                hexagon.color = FOREST_COLOR
            elif terrain == "Pasture":
                hexagon.color = PASTURE_COLOR
            elif terrain == "Grain":
                hexagon.color = GRAIN_COLOR
            elif terrain == "Clay":
                hexagon.color = CLAY_COLOR
            elif terrain == "Hill":
                hexagon.color = HILL_COLOR
            elif terrain == "Desert":
                hexagon.color = DESERT_COLOR
            
            
            hexagon.number = number


    def generate_hexagonal_grid(self, radius):
        hexes = []
        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                s = -q - r
                if abs(s) <= radius:
                    hexes.append(self.Hexagon(q, r, s))
        
        # Prepare terrains with the appropriate counts
        terrain_counts = {
            "Forest": 4,
            "Pasture": 4,
            "Grain": 4,
            "Clay": 3,
            "Ore": 3,
            "Desert": 1
        }

        terrains = []
        for terrain, count in terrain_counts.items():
            terrains.extend([terrain] * count)
            
        numbers = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        import random
        random.shuffle(terrains)
        self.assign_terrains_to_hexes(hexes, terrains, numbers)
        
        return hexes
    
    def closest_edge(self, point):
        nearest_edge = None
        nearest_edge_midpoint = None
        nearest_distance = float('inf')

        for hexagon in self.hexes:
            for edge in hexagon.get_edges():
                midpoint = ((edge[0][0] + edge[1][0]) / 2, (edge[0][1] + edge[1][1]) / 2)
                distance = math.dist(point, midpoint)
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_edge = edge
                    nearest_edge_midpoint = midpoint

        return nearest_edge, nearest_edge_midpoint

    def closest_corner(self, point):
        nearest_corner = None
        nearest_distance = float('inf')

        for hexagon in self.hexes:
            for corner in hexagon.get_corners():
                distance = math.dist(point, corner)
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_corner = corner

        return nearest_corner

    def place_settlement(self, position, color):
        self.settlements.append((position, color))
        self.current_observation["settlements"][position] = {
            "color": color,
            "position": position
        }

    def place_road(self, start, end, color):
        self.roads.append((start, end, color))
        self.current_observation["roads"][(start, end)] = {
            "color": color,
            "start": start,
            "end": end
        }

    
    
    def is_connected_road(self, midpoint, player_color):
        # Check if the road is connected to any settlements of the same color
        for settlement in self.settlements:
            if math.dist(midpoint, settlement[0]) < HEX_WIDTH / 2 and settlement[1] == player_color:
                return True
        
        # Check if the road is connected to another road of the same color
        for road in self.roads:
            if (math.dist(midpoint, road[0]) < HEX_WIDTH / 2 or math.dist(midpoint, road[1]) < HEX_WIDTH / 2) and road[2] == player_color:
                return True
        
        return False
    
    def handle_mouse_click(self, mouse_pos, button, player_color, placing_settlement):
        nearest_corner = self.closest_corner(mouse_pos)
        nearest_edge, nearest_edge_midpoint = self.closest_edge(mouse_pos)

        if nearest_corner and nearest_edge:
            corner_distance = math.dist(mouse_pos, nearest_corner)
            edge_distance = math.dist(mouse_pos, nearest_edge_midpoint)

            if corner_distance < edge_distance:
                # Closer to a corner, consider placing a settlement
                if button == 1 and placing_settlement:  # Left click for settlements
                    # Convert corner position to hex for distance comparison
                    # corner_hex = self.pixel_to_hex(nearest_corner)
                    for s in self.settlements:
                        if math.dist(nearest_corner, s[0]) < int(HEX_WIDTH):
                            return False
                    # if all(self.hex_distance(corner_hex, self.pixel_to_hex(s[0])) >= 1 for s in self.settlements):
                    self.place_settlement(nearest_corner, player_color)
                    
                    return True
            else:
                # Closer to an edge, consider placing a road
                if button == 1 and not placing_settlement:  # Left click for roads
                    if self.is_connected_road(nearest_edge_midpoint, player_color):
                        # if self.temp_road_start is None:
                        #     self.temp_road_start = nearest_edge
                        # else:
                        self.place_road(nearest_edge[0], nearest_edge[1], player_color)
                        self.temp_road_start = None
                        
                        return True

        return False

    def get_highlight(self, mouse_pos):
        nearest_corner = self.closest_corner(mouse_pos)
        nearest_edge, nearest_edge_midpoint = self.closest_edge(mouse_pos)

        if nearest_corner and nearest_edge:
            corner_distance = math.dist(mouse_pos, nearest_corner)
            edge_distance = math.dist(mouse_pos, nearest_edge_midpoint)

            if corner_distance < edge_distance:
                return nearest_corner, None
            else:
                return None, nearest_edge
        else:
            return nearest_corner, nearest_edge

    
    def calculate_scores(self):
        scores = {color: 0 for color in self.player_colors}
        
        # Points for settlements
        for settlement in self.settlements:
            position, color = settlement
            scores[color] += 1
        
        # Points for roads
        connected_roads = {}
        for road in self.roads:
            start, end, color = road
            # Check if this road connects two settlements
            if any(math.dist(start, s[0]) < 10 for s in self.settlements if s[1] == color) and \
               any(math.dist(end, s[0]) < 10 for s in self.settlements if s[1] == color):
                road_length = math.dist(start, end)
                if color not in connected_roads:
                    connected_roads[color] = []
                connected_roads[color].append(road_length)
        
        # Add road lengths to scores
        for color, roads in connected_roads.items():
            for length in roads:
                scores[color] += int(length // HEX_WIDTH)  # Convert pixel distance to "hex steps"

        return scores
    
    def get_all_available_corners(self):
        corners = set()
        for hex in self.hexes:
            for corner in hex.get_corners():
                corners.add(corner)
        
        # Remove corners that are already occupied by settlements
        occupied_corners = set(settlement[0] for settlement in self.settlements)
        available_corners = corners - occupied_corners
        
        return list(available_corners)
    
    def to_dict(self):
        return {
            "hexagons": self.current_observation["hexagons"],
            "settlements": self.current_observation["settlements"],
            "roads": self.current_observation["roads"],
            "temp_road_start": self.temp_road_start
        }
        
    
    def to_dict_flask(self):
        # Convert hexagons
        hexagons_dict = {
            str(key): {
                'position': list(value["position"]),
                'color': value["color"],
                'number': value["number"]
            } for key, value in self.current_observation["hexagons"].items()
        }

        # Convert settlements
        settlements_dict = {
            str(key): {
                'position': list(value["position"]),
                'color': value["color"]
            } for key, value in self.current_observation["settlements"].items()
        }

        # Convert roads
        roads_dict = {
            str(key): {
                'start': list(value["start"]),
                'end': list(value["end"]),
                'color': value["color"]
            } for key, value in self.current_observation["roads"].items()
        }

        return {
            'hexagons': hexagons_dict,
            'settlements': settlements_dict,
            'roads': roads_dict
        }


class CatanPygameUI:
    def __init__(self, screen, map_data, player_name, player_color):
        self.screen = screen
        self.map_data = map_data
        self.player_name = player_name
        
        self.player_names = ["red", "green", "blue"]
        self.player_color = player_color
        self.player_colors = [RED, GREEN, BLUE]
        self.font = pygame.font.Font(None, 36)
        self.number_font = pygame.font.Font(None, 24)  # Smaller font for numbers

    def draw_hexes(self):
        
        for hex_data in self.map_data["hexagons"].values():
            x, y = hex_data["position"]
            points = [
                (x + HEX_RADIUS * math.cos(math.pi / 3 * i + math.pi / 6),
                 y + HEX_RADIUS * math.sin(math.pi / 3 * i + math.pi / 6))
                for i in range(6)
            ]
            pygame.draw.polygon(self.screen, hex_data['color'], points, 0)
            pygame.draw.polygon(self.screen, BLACK, points, 2)
            
            if hex_data['number']:
                number_text = self.number_font.render(str(hex_data['number']), True, BLACK)
                text_rect = number_text.get_rect(center=(x, y))
                self.screen.blit(number_text, text_rect)
            else:
                # Draw a robber
                number_text = self.number_font.render("Robber", True, BLACK)
                text_rect = number_text.get_rect(center=(x, y))
                self.screen.blit(number_text, text_rect)
            

    def draw_settlements(self):
        for settlement_data in self.map_data["settlements"].values():
            pygame.draw.circle(self.screen, settlement_data["color"], settlement_data["position"], 10)

    def draw_roads(self):
        for road_data in self.map_data["roads"].values():
            pygame.draw.line(self.screen, road_data["color"], road_data["start"], road_data["end"], 5)

    def draw_temp_road(self):
        if self.map_data["temp_road_start"]:
            pygame.draw.line(self.screen, RED, self.map_data["temp_road_start"][0], self.map_data["temp_road_start"][1], 5)

    
    def draw_scores(self, scores):
        y_offset = 50
        for idx, color in enumerate(self.player_names):
            score_text = f"{self.player_names[idx]}: {scores[color]}"
            text_surface = self.font.render(score_text, True, self.player_colors[idx])
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 30

    def draw(self, scores):
        self.screen.fill(LIGHT_BLUE)
        self.draw_hexes()
        self.draw_settlements()
        self.draw_roads()
        self.draw_temp_road()
        
        # Draw current player name
        player_text = self.font.render(self.player_name, True, BLACK)
        self.screen.blit(player_text, (10, 10))
        
        # Draw scores
        self.draw_scores(scores)


def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Catan Game")

    map_radius = 2
    catan_map = CatanMap(map_radius)

    # Initial player setup
    current_player_index = 0
    player_color = catan_map.player_colors[current_player_index]
    player_name = catan_map.player_names[current_player_index]
    scores = catan_map.calculate_scores()
    ui = CatanPygameUI(screen, catan_map.to_dict(), player_name, player_color)

    placing_settlement = True  # Start by placing settlements
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if catan_map.handle_mouse_click(event.pos, event.button, player_color, placing_settlement):
                    if placing_settlement:
                        placing_settlement = False
                    else:
                        current_player_index = (current_player_index + 1) % NUM_PLAYERS
                        player_color = catan_map.player_colors[current_player_index]
                        player_name = catan_map.player_names[current_player_index]
                        placing_settlement = True

                    scores = catan_map.calculate_scores()
                    ui = CatanPygameUI(screen, catan_map.to_dict(), player_name, player_color)

        # Print all available hex corners
        print("Available hex corners:")
        for i, corner in enumerate(catan_map.get_all_available_corners()):
            print(f"Corner {i}: {corner}")

        # Highlight nearest corner or edge
        mouse_pos = pygame.mouse.get_pos()
        highlight_corner, highlight_edge = catan_map.get_highlight(mouse_pos)

        ui.draw(scores)

        if highlight_corner:
            pygame.draw.circle(screen, YELLOW, highlight_corner, 10, 2)
        elif highlight_edge:
            pygame.draw.line(screen, YELLOW, highlight_edge[0], highlight_edge[1], 5)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

