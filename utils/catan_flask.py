from flask import Flask, jsonify, request, send_file, render_template_string
from utils.catan_utils import CatanMap, CatanPygameUI, PLAYER_COLORS, PLAYER_NAMES  # Adjust the import to your actual file structure
import pygame

app = Flask(__name__)

# Initialize game state
map_radius = 2
catan_map = CatanMap(map_radius)
current_player_index = 0
placing_settlement = True

# Path to save the game image
IMAGE_PATH = 'game_state.png'

def generate_game_image(catan_map, filename='game_state.png'):
    pygame.init()
    screen = pygame.Surface((800, 600))  # Create a surface instead of a window

    current_player_index = 0
    player_color = PLAYER_COLORS[current_player_index]
    player_name = PLAYER_NAMES[current_player_index]
    scores = catan_map.calculate_scores()
    ui = CatanPygameUI(screen, catan_map.to_dict(), player_name, player_color)

    ui.draw(scores)
    # Your existing drawing code here, e.g.:
    # screen.fill((255, 255, 255))
    # draw hexagons, settlements, roads, etc.
    # Example:
    # for hex in catan_map.hexagons.values():
    #     pygame.draw.polygon(screen, hex.color, hex.points)

    pygame.image.save(screen, filename)  # Save the surface as an image file
    pygame.quit()

@app.route('/')
def index():
    # Generate the game image
    generate_game_image(catan_map, IMAGE_PATH)
    
    # Serve the HTML page with the image
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Catan Game</title>
        </head>
        <body>
            <h1>Catan Game</h1>
            <img src="{{ url_for('static', filename='game_state.png') }}" alt="Game State">
        </body>
        </html>
    ''')

@app.route('/update')
def update():
    generate_game_image(catan_map, IMAGE_PATH)
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Catan Game</title>
        </head>
        <body>
            <h1>Catan Game</h1>
            <img src="{{ url_for('static', filename='game_state.png') }}" alt="Game State">
        </body>
        </html>
    ''')

@app.route('/click', methods=['POST'])
def handle_click():
    global current_player_index, placing_settlement

    data = request.json
    pos = data['pos']
    button = data['button']

    player_color = PLAYER_COLORS[current_player_index]

    if catan_map.handle_mouse_click(pos, button, player_color, placing_settlement):
        if placing_settlement:
            placing_settlement = False
        else:
            current_player_index = (current_player_index + 1) % len(PLAYER_COLORS)
            placing_settlement = True
    
    # Update the game image
    generate_game_image(catan_map, IMAGE_PATH)

    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)