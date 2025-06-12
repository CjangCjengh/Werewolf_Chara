import matplotlib.pyplot as plt
import matplotlib.patches as patches
# Define the figure and axis
# from logger import logger


def viz_image_pattern():
    fig, ax = plt.subplots(figsize=(6, 6))

    # Define colors for the tiles
    colors = {
        'red': '#FF0000',
        'yellow': '#FFFF00',
        'purple': '#000000',
        'white': '#FFFFFF',
        'empty': 'none'
    }

    # Define the color pattern for each row
    color_pattern = [
        ['empty', 'empty', 'empty', 'empty', 'empty'],
        ['red', 'red', 'red', 'red'],
        ['empty', 'white', 'empty'],
        ['yellow', 'yellow'],
        ['purple']
    ]

    # Draw the grid
    for i, row in enumerate(color_pattern):
        for j, color in enumerate(row):
            # Calculate the position
            x = j
            y = len(color_pattern) - i - 1
            # Create a rectangle patch
            rect = patches.Rectangle((x, y), 1, 1, edgecolor='purple', facecolor=colors[color])
            # Add the patch to the axis
            ax.add_patch(rect)

    # Add the number "0"
    ax.text(-1.5, len(color_pattern) - 2, "0", fontsize=40, verticalalignment='center', horizontalalignment='center')

    # Set limits and aspect
    ax.set_xlim(-2, 6)
    ax.set_ylim(-1, 6)
    ax.set_aspect('equal')


    ax.axis('off')

    # Show the plot
    plt.show()


def validate_dice(valid_dices):
    """Decorator to validate the dice used in the action."""
    def decorator(func):
        def wrapper(self, role, action, dice, *args, **kwargs):
            if dice not in valid_dices:
                # logger.error(f"Invalid dice: {dice}")
                return
            return func(self, role, action, dice, *args, **kwargs)
        return wrapper
    return decorator